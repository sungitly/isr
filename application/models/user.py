# -*- coding: utf-8 -*-
from datetime import datetime

from flask.helpers import locked_cached_property
from sqlalchemy import Column, String, desc, distinct
from werkzeug.exceptions import Forbidden

from application.cache import cache, LONG_CACHE, SHORT_CACHE
from application.events import sales_status_changed
from application.models.reception import Reception
from application.nutils.menu import L1_SETTINGS, L1_SALES_RESULT, L1_SALES_PROCESS, \
    L1_SALES_MGMT, L1_OPS_DASHBOARD, L2_SALES_DASHBOARD, L2_SETTINGS, \
    L1_SALES_MANAGER_DASHBOARD, L1_INVENTORY_MGMT, L1_RADAR
from application.redisstore import redis_store
from application.utils import DATE_FORMAT, SECONDS_OF_DAY, convert_int
from .base import db, BaseMixin, ActiveMixin, get_or_create
from .middle import StoreUserRoleScope
from .role import Role
from .store import Store

USER_ROLE_STORE_MANAGER = 'manager'
USER_ROLE_STORE_SALES = 'sales'
USER_ROLE_STORE_RECEPTIONIST = 'receptionist'
USER_ROLE_STORE_OPS = 'ops'
USER_ROLE_STORE_STOCKMAN = 'stockman'

INSTORE_NO_RX_LEAD = u'无效接待'


class RoleEndpointMenu(object):
    def __init__(self, id, role, endpoint_fun, menu):
        self.id = id
        self.role = role
        self.endpoint_fun = endpoint_fun
        self.menu = menu


def make_return_fun(value):
    return lambda: value


def make_raise_fun(exception):
    def fun():
        raise exception

    return fun


_role_to_endpoint_menu = [
    RoleEndpointMenu(USER_ROLE_STORE_OPS,
                     'ops',
                     make_return_fun('ops.isr'),
                     [L1_OPS_DASHBOARD]),
    RoleEndpointMenu(USER_ROLE_STORE_MANAGER,
                     'manager',
                     make_return_fun('user.dashboard'),
                     [L1_SALES_MANAGER_DASHBOARD,
                      L1_SALES_RESULT,
                      L1_SALES_PROCESS,
                      L1_SALES_MGMT,
                      L1_RADAR,
                      L1_SETTINGS]),
    RoleEndpointMenu(USER_ROLE_STORE_SALES,
                     'sales',
                     make_return_fun('customers.customers'),
                     [L2_SALES_DASHBOARD, L2_SETTINGS]),
    RoleEndpointMenu(USER_ROLE_STORE_STOCKMAN,
                     'stockman',
                     make_return_fun('inventories.inventories'),
                     [L1_INVENTORY_MGMT, L2_SETTINGS])
]
_role_to_endpoint_menu_default = RoleEndpointMenu(-1, 'default', make_raise_fun(Forbidden()), [L1_SETTINGS])


class User(db.Model, ActiveMixin, BaseMixin):
    __tablename__ = 'user'

    username = Column(String(50))
    email = Column(String(50), index=True)
    mobile = Column(String(50), index=True)
    title = Column(String(200))
    avatar = Column(String(200), default='default.png')

    system = Column(String(200), default='bmw')  # 从哪个系统登录!! 'bmw', 'ucenter'

    def update_permission(self, store_user_role_scope):
        '''
        根据服务器返回的值更新自己的权限,
        权限中出现未定义的store, rule会自动创建
        '''
        StoreUserRoleScope.from_json(self, store_user_role_scope)
        db.session.commit()  # 注意这里需要commit

    def update_permission_auth(self, store_id, store_name, type, roles):
        '''
        兼容老系统, 变换成新的表结构
        '''
        type_to_scope_type = {
            6: 'store',
            7: 'individual',
            8: 'individual',
            101: 'store'
        }
        type_to_role_title = {
            6: 'manager',
            7: 'sales',
            8: 'receptionist',
            101: 'ops'
        }
        if roles == 'manager' and type in (7, 8):
            StoreUserRoleScope.from_auth(self, store_id, store_name, 'manager', 'store')
            db.session.commit()
            StoreUserRoleScope.from_auth(self, store_id, store_name, 'sales', 'individual')
            db.session.commit()
        else:
            StoreUserRoleScope.from_auth(self, store_id, store_name, type_to_role_title[type], type_to_scope_type[type])
            db.session.commit()

    def from_auth(self, auth):
        self.id = auth['id']
        self.username = auth['username']
        self.email = auth['email']
        self.title = auth.get('title')
        self.system = 'bmw'
        self.activate()
        db.session.add(self)

        if self.id is not None:
            StoreUserRoleScope.drop_by_userid(self.id)

        if auth.get('stores'):
            stores = auth.get('stores')
            if len(stores) >= 1:
                store_id = stores[0].get('id')
                storename = stores[0].get('storename')
                roles = auth.get('roles')
                type = auth.get('user_type')
                self.update_permission_auth(store_id, storename, type, roles)

    @classmethod
    def from_ucenter(cls, data):
        '''
        从ucenter构建用户, 用户权限
        '''
        user_data = data.user
        store_user_role_scopes = data.store_user_role_scopes

        user_id = user_data['id']

        user, _ = get_or_create(User, id=user_id)
        user.system = 'ucenter'
        if 'active' in user_data and convert_int(user_data.get('active')) <= 0:
            user.deactivate()
        else:
            user.activate()

        if user_id is not None:
            StoreUserRoleScope.drop_by_userid(user_id)

        for filed in ['id', 'username', 'email', 'mobile']:
            if filed in user_data:
                setattr(user, filed, user_data[filed])

        if 'profile' in user_data:
            profile = user_data['profile']
            for filed in ['title', 'avatar']:
                if filed in profile:
                    setattr(user, filed, profile[filed])

        db.session.add(user)
        for p in store_user_role_scopes:
            user.update_permission(p)
        return user

    @classmethod
    def find_all_user_type_by_store(cls, store_id, role_title):
        role = Role.find_by_title(role_title)
        if not role:
            return []

        role_id = role.id
        query_user_ids = db.session.query(StoreUserRoleScope.user_id) \
            .filter(StoreUserRoleScope.role_id == role_id) \
            .filter(StoreUserRoleScope.store_id == store_id)

        query = cls.query.filter(cls.id.in_(query_user_ids)) \
            .filter(cls.filter_active()) \
            .order_by(desc(cls.updated_on))
        return query.all()

    @classmethod
    def find_all_sales_by_store(cls, store_id):
        return cls.find_all_user_type_by_store(store_id, USER_ROLE_STORE_SALES)

    @classmethod
    def find_all_receptionist_by_store(cls, store_id):
        return cls.find_all_user_type_by_store(store_id, USER_ROLE_STORE_RECEPTIONIST)

    @classmethod
    def find_all_by_sales_name(cls, username):
        '''
        :param username: sales name in user table
        :return: all columns which matched
        '''
        role = Role.find_by_title(USER_ROLE_STORE_SALES)
        if not role:
            return []

        role_id = role.id
        session = db.session
        query_role = session.query(StoreUserRoleScope.user_id).filter(StoreUserRoleScope.role_id == role_id)

        query = cls.query.filter(cls.username == username) \
            .filter(cls.filter_active()) \
            .filter(cls.id.in_(query_role)) \
            .order_by(desc(cls.updated_on))
        return query.all()

    @classmethod
    def find_by_sales_name(cls, username, store_id):
        role = Role.find_by_title(USER_ROLE_STORE_SALES)
        if not role:
            return []

        role_id = role.id

        query_user_ids = db.session.query(StoreUserRoleScope.user_id).filter(
            StoreUserRoleScope.role_id == role_id).filter(StoreUserRoleScope.store_id == store_id)

        query = cls.query.filter(cls.username == username).filter(cls.id.in_(query_user_ids)).filter(
            cls.filter_active()).order_by(desc(cls.updated_on))
        return query.first()

    @staticmethod
    @cache.memoize(timeout=SHORT_CACHE)
    def get_all_sales_by_store_from_cache(store_id):
        return User.find_all_sales_by_store(store_id)

    @staticmethod
    @cache.memoize(timeout=SHORT_CACHE)
    def get_all_receptionist_by_store_from_cache(store_id):
        return User.find_all_receptionist_by_store(store_id)

    @staticmethod
    @cache.memoize(timeout=LONG_CACHE)
    def get_user_by_id_from_cache(user_id):
        return User.find(user_id)

    def get_menu_items(self):
        return self._get_menu_items(self.role_titles)

    @staticmethod
    def _get_menu_items(role_titles):
        menu_items = []
        # combine roles menu
        for role in role_titles:
            role_menu_items_list = [m for m in _role_to_endpoint_menu if m.role == role]
            if len(role_menu_items_list) == 0:
                continue
            else:
                menu_items = menu_items + [m for m in role_menu_items_list[0].menu if m not in menu_items]

        if len(menu_items) > 0:
            # hack to move setting menu to the end
            if L1_SETTINGS in menu_items:
                menu_items.remove(L1_SETTINGS)
                menu_items.append(L1_SETTINGS)
                # if both L1 and L2 settings exist. Remove L2 settings
                if L2_SETTINGS in menu_items:
                    menu_items.remove(L2_SETTINGS)
            elif L2_SETTINGS in menu_items:
                menu_items.remove(L2_SETTINGS)
                menu_items.append(L2_SETTINGS)

            if L1_RADAR in menu_items:
                from application.session import get_or_set_store_id
                current_store_id = get_or_set_store_id()
                from application.models.setting import StoreSetting
                if not StoreSetting.is_radar_avail(current_store_id):
                    menu_items.remove(L1_RADAR)

            return menu_items
        else:
            return _role_to_endpoint_menu_default.menu

    def dashboard_endpoint(self):
        role_titles = self.role_titles  # cache
        for item in _role_to_endpoint_menu:
            if item.role in role_titles:
                return item.endpoint_fun()
        return _role_to_endpoint_menu_default.endpoint_fun()

    def is_sales(self):
        '''
        兼容以前
        '''
        return USER_ROLE_STORE_SALES in self.role_titles

    def is_receptionist(self):
        '''
        兼容以前
        '''
        return USER_ROLE_STORE_RECEPTIONIST in self.role_titles

    def is_role_in_store_id(self, store_id, role_title):
        role = Role.find_by_title(role_title)
        if not role:
            return False

        query = StoreUserRoleScope.query \
            .filter(StoreUserRoleScope.store_id == store_id) \
            .filter(StoreUserRoleScope.role_id == role.id) \
            .filter(StoreUserRoleScope.user_id == self.id)
        item = query.first()
        return bool(item)

    def is_sales_in_store(self, store_id):
        return self.is_role_in_store_id(store_id, USER_ROLE_STORE_SALES)

    def is_receptionist_in_store(self, store_id):
        return self.is_role_in_store_id(store_id, USER_ROLE_STORE_RECEPTIONIST)

    @property
    def role_titles(self):
        query = db.session.query(distinct(StoreUserRoleScope.role_id)) \
            .filter(StoreUserRoleScope.user_id == self.id)

        query_roles = db.session.query(Role.title).filter(Role.id.in_(query))
        roles = query_roles.all()

        return [role[0] for role in roles]

    def roles_in_store(self, store_id):
        '''
        获取对特定店的权限
        '''
        query_role_ids = db.session.query(distinct(StoreUserRoleScope.role_id)) \
            .filter(StoreUserRoleScope.user_id == self.id) \
            .filter(StoreUserRoleScope.store_id == store_id)

        query_role_title = db.session.query(Role.title) \
            .filter(Role.id.in_(query_role_ids))
        roles = query_role_title.all()
        return [role[0] for role in roles]

    def getDataScope(self, object, store_id):
        scope = dict()
        if object in ('customer'):
            role_titles = self.roles_in_store(store_id)
            if USER_ROLE_STORE_MANAGER in role_titles:
                scope['store_id'] = store_id
            elif USER_ROLE_STORE_SALES in role_titles:
                scope['sales_id'] = self.id
            else:
                raise Forbidden()
        return scope

    def get_all_stores(self):

        query_store_ids = db.session.query(distinct(StoreUserRoleScope.store_id)) \
            .filter(StoreUserRoleScope.user_id == self.id)
        query_store = db.session.query(Store) \
            .filter(Store.id.in_(query_store_ids))
        return query_store.all()

    def get_default_store_id(self):
        '''
        默认管理的一个store_id
        '''
        query_store_ids = db.session.query(distinct(StoreUserRoleScope.store_id)) \
            .filter(StoreUserRoleScope.user_id == self.id)
        res = query_store_ids.first()
        if not res:
            return
        return res[0]

    def has_role_in_current_store(self, role):
        from application.session import get_or_set_store_id
        return self.is_role_in_store_id(get_or_set_store_id(), role)

    @locked_cached_property
    def store_id(self):
        return self.get_default_store_id()

    @locked_cached_property
    def stores(self):
        query_store_ids = db.session.query(distinct(StoreUserRoleScope.store_id)) \
            .filter(StoreUserRoleScope.user_id == self.id)
        query_store = db.session.query(Store) \
            .filter(Store.id.in_(query_store_ids))
        res = []
        stores = query_store.all()
        for store in stores:
            query_role_ids = db.session.query(distinct(StoreUserRoleScope.role_id)) \
                .filter(StoreUserRoleScope.user_id == self.id) \
                .filter(StoreUserRoleScope.store_id == store.id)

            query_roles = db.session.query(Role.title) \
                .filter(Role.id.in_(query_role_ids))

            roles = query_roles.all()
            if not roles:
                continue

            res.append({
                'id': store.id,
                'name': store.name,
                'roles': [role[0] for role in roles]
            })
        return res


class SuperUser(User):
    def is_role_in_store_id(self, store_id, role_title):
        return True


class Visitor(User):
    def is_role_in_store_id(self, store_id, role_title):
        return False


class SalesStatus(object):
    valid_status = ('free', 'busy', 'leave')

    # type: hash
    sales_status_per_store_per_day = 'isr:sales:status:store:%s:%s'

    @staticmethod
    def get_sales_status_key(store_id):
        return SalesStatus.sales_status_per_store_per_day % (store_id, datetime.today().strftime(DATE_FORMAT))

    @staticmethod
    def get_all_sales_status(store_id):
        name = SalesStatus.get_sales_status_key(store_id)
        if not redis_store.exists(name):
            SalesStatus.init_sales_status(name, store_id)

        return redis_store.hgetall(name)

    @staticmethod
    def get_sales_status(store_id, sales_id):
        name = SalesStatus.get_sales_status_key(store_id)
        return redis_store.hget(name, sales_id)

    @staticmethod
    def set_sales_status(store_id, sales_id, status='free'):
        name = SalesStatus.get_sales_status_key(store_id)
        if not redis_store.exists(name):
            SalesStatus.init_sales_status(name, store_id)

        redis_store.hset(name, sales_id, status)

        sales_status_changed.send(store_id=store_id)

    @staticmethod
    def set_sales_status_from_mapping(store_id, sales_status_mapping):
        if sales_status_mapping and len(sales_status_mapping) > 0:
            name = SalesStatus.get_sales_status_key(store_id)
            if not redis_store.exists(name):
                SalesStatus.init_sales_status(name, store_id)

            redis_store.hmset(name, sales_status_mapping)

    @staticmethod
    def init_sales_status(name, store_id):
        sales = User.get_all_sales_by_store_from_cache(long(store_id))
        if len(sales) > 0:
            sales_status_mapping = {sale.id: 'free' for sale in sales}

            redis_store.hmset(name, sales_status_mapping)
            redis_store.expire(name, SECONDS_OF_DAY)

    @staticmethod
    def del_sales_status(store_id, sales_id):
        name = SalesStatus.get_sales_status_key(store_id)
        redis_store.hdel(name, sales_id)

    @staticmethod
    def update_sales_status(store_id, sales_id, status=None):
        old_status = SalesStatus.get_sales_status(store_id, sales_id)

        if status is None and old_status == 'leave':
            return

        if status is None:
            if Reception.exist_sales_incomplete_receptions_of_today(sales_id):
                status = 'busy'
            else:
                status = 'free'

        SalesStatus.set_sales_status(store_id, sales_id, status)

    @staticmethod
    def reset_all_sales_status(store_id):
        existing_sales_status = SalesStatus.get_all_sales_status(store_id)
        incomplete_rx_count_by_sales = Reception.count_all_incomplete_of_today_by_sales(store_id)
        new_sales_status = {str(r[0]): 'busy' if r[1] > 0 else 'free' for r in incomplete_rx_count_by_sales}

        for sales_id, sales_status in existing_sales_status.iteritems():
            if sales_status != 'leave':
                existing_sales_status[sales_id] = new_sales_status.get(sales_id, 'free')
        SalesStatus.set_sales_status_from_mapping(store_id, existing_sales_status)


class SalesLastRxTime(object):
    # type: hash
    sales_status_per_store_per_day = 'isr:sales:rxtime:store:%s:%s'

    @staticmethod
    def get_sales_last_rxtime_key(store_id):
        return SalesLastRxTime.sales_status_per_store_per_day % (store_id, datetime.today().strftime(DATE_FORMAT))

    @staticmethod
    def set_sales_rxtime(store_id, sales_id, rxtime):
        name = SalesLastRxTime.get_sales_last_rxtime_key(store_id)
        redis_store.hset(name, sales_id, rxtime)

    @staticmethod
    def get_all_sales_rxtime(store_id):
        name = SalesLastRxTime.get_sales_last_rxtime_key(store_id)
        return redis_store.hgetall(name)
