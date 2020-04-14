# -*- coding: utf-8 -*-
from urlparse import urljoin

class MenuItem(object):
    def __init__(self, name, url, desc, icon_css='', sub_menus=None):
        self.name = name
        self._url = url
        self.desc = desc
        self.icon_css = icon_css
        self.sub_menus = sub_menus if sub_menus else []
        self.parent = None

    @property
    def url(self):
        if self.parent is None:
            return self._url
        base_url = self.parent.url
        return urljoin(base_url, self._url)

    def append_sub_menu(self, menu):
        menu.parent = self
        self.sub_menus.append(menu)

    def extend_sub_menu(self, menus):
        for menu in menus:
            menu.parent = self
        self.sub_menus.extend(menus)

    def has_sub_menu(self):
        return len(self.sub_menus) > 0

    def contains(self, menu):
        if menu is self:
            return True
        if menu.parent is self:
            return True
        if self.name == menu.name:
            return True
        elif self.has_sub_menu():
            for sub_menu in self.sub_menus:
                if sub_menu.contains(menu):
                    return True


HOME_MENU = MenuItem('home', '/', u'主页')

# Sales Manager Menu Items
USER_RT_DATA = MenuItem('user_rt_data', '/user/dashboard', u'实时数据')
USER_MORNING_CALL = MenuItem('user_mc', '/user/mc', u'晨会资料')
USER_EVENING_CALL = MenuItem('user_ec', '/user/ec', u'夕会资料')
RX_VIEW = MenuItem('receptions_view', '/receptions/', u'接待查询')
APPTS_VIEW = MenuItem('appts_view', '/appointments/', u'预约查询')
CALL_LOG = MenuItem('call_log', '/calllogs/', u'通话记录')
CUSTOMER_MGMT = MenuItem('cust_mgmt', '/customers/', u'客户管理')
ORDERS_MGMT = MenuItem('orders_mgmt', '/orders/', u'订单管理')
CAMPAIGN_MGMT = MenuItem('campaign_mgmt', '/campaigns/', u'活动管理')
LEADS_VIEW = MenuItem('leads_view', '/leads/', u'未接待客流')

L1_SALES_MANAGER_DASHBOARD = MenuItem('sm_dashboard', '/user/dashboard', u'展厅动态', 'fa-th-large')
L1_SALES_MANAGER_DASHBOARD.extend_sub_menu(
    (USER_RT_DATA, USER_MORNING_CALL, USER_EVENING_CALL, RX_VIEW, APPTS_VIEW, CALL_LOG, CUSTOMER_MGMT, ORDERS_MGMT,
     CAMPAIGN_MGMT, LEADS_VIEW))

INV_MGMT = MenuItem('inv_mgmt', '/inventories/', u'库存管理')
L1_INVENTORY_MGMT = MenuItem('inv_dashboard', '/inventories/', u'库存管理', 'fa-database')
L1_INVENTORY_MGMT.append_sub_menu(INV_MGMT)

SR_TCR = MenuItem('sr_tcr', '/stats/tcr', u'TA完成率')  # target completion rate
SR_CR = MenuItem('sr_cr', '/stats/cr', u'转化率')  # conversion rate
SR_RR = MenuItem('sr_rr', '/stats/rr', u'重购及老客户推荐率')  # returning rate

L1_SALES_RESULT = MenuItem('sales_result', '/stats/tcr', u'销售结果', 'fa-calculator')
L1_SALES_RESULT.extend_sub_menu([SR_TCR, SR_CR, SR_RR])

SP_FR = MenuItem('sp_fr', '/stats/fr', u'留档率')  # filing rate
SP_ACR = MenuItem('sp_acr', '/stats/acr', u'邀约完成率')  # appointment completion rate
SP_TDR = MenuItem('sp_tdr', '/stats/tdr', u'试驾率')  # test drive rate
SP_ICD = MenuItem('sp_icd', '/stats/icd', u'意向车型分布')  # intent-car distribution

L1_SALES_PROCESS = MenuItem('sales_process', '/stats/fr', u'销售过程', 'fa-repeat')
L1_SALES_PROCESS.extend_sub_menu((SP_FR, SP_ACR, SP_TDR, SP_ICD))

SM_SC = MenuItem('sm_sc', '/stats/sc', u'销售顾问')  # sales consultant
SM_UOC = MenuItem('sm_uoc', '/stats/uoc', u'未成交客户')  # unordered customer
SM_OC = MenuItem('sm_oc', '/stats/oc', u'成交客户')  # ordered customer
SM_HC = MenuItem('sm_hc', '/stats/hc', u'休眠客户')  # hibernated customer

L1_SALES_MGMT = MenuItem('sales_mgmt', '/stats/sc', u'销售管理', 'fa-users')
L1_SALES_MGMT.extend_sub_menu([SM_SC, SM_UOC, SM_OC])

MODIFY_PASSWORD = MenuItem('modify_password', '/settings/security', u'修改密码')
TARGET_SETTINGS = MenuItem('target_setting', '/settings/ta', u'TA设定')

L1_SETTINGS = MenuItem('settings', '/settings/ta', u'设置', 'fa-gears')
L1_SETTINGS.extend_sub_menu([TARGET_SETTINGS, MODIFY_PASSWORD])

# Ops Menu Items
OPS_OVERVIEW = MenuItem('ops_overview', '/ops/overview', u'运营简报')
STORE_STATS_SUMMARY = MenuItem('store_stats_summary', '/ops/isr', u'超级前台')
STORE_RADAR_SUMMARY = MenuItem('store_radar_summary', '/ops/radar', u'客流雷达')
RADAR_STATUS_SUMMARY = MenuItem('radar_status_summary', '/ops/radar/status', u'雷达状态')
APPS_MGMT_SUMMARY = MenuItem('apps_mgmt', '/ops/apps', u'应用管理')
LOOKUPVALUE_MGMT_SUMMARY = MenuItem('lookupvalue_mgmt', '/ops/lookupvalue', u'车型管理')

L1_OPS_DASHBOARD = MenuItem('ops_dashboard', '/ops/isr', u'仪表盘', 'fa-th-large')
L1_OPS_DASHBOARD.extend_sub_menu(
    [STORE_STATS_SUMMARY, STORE_RADAR_SUMMARY, OPS_OVERVIEW, RADAR_STATUS_SUMMARY, APPS_MGMT_SUMMARY, LOOKUPVALUE_MGMT_SUMMARY])

# Sales Menu Items
L2_SALES_DASHBOARD = MenuItem('sm_dashboard', '/customers/', u'销售管理')
L2_SALES_DASHBOARD.extend_sub_menu([CUSTOMER_MGMT])

L2_SETTINGS = MenuItem('settings', '/settings/security', u'设置')
L2_SETTINGS.extend_sub_menu([MODIFY_PASSWORD])

L1_RADAR = MenuItem('manager_radar', '/manager/radar/', u'雷达数据', 'fa-signal')
L2_RADAR_TENDENCY  = MenuItem('manager_radar_tendency', 'tendency', u'总体趋势分析', 'fa-signal')
L2_RADAR_STRUCTURE = MenuItem('manager_radar_structure', 'structure', u'客流分析', 'fa-signal')
L2_RADAR_MULTI     = MenuItem('manager_radar_multi', 'multi', u'高意向客流分析', 'fa-signal')

L1_RADAR.extend_sub_menu([L2_RADAR_TENDENCY,
                          L2_RADAR_STRUCTURE,
                          L2_RADAR_MULTI])
