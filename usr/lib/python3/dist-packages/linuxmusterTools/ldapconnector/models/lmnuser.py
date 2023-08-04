from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import ldap
import re
from .lmnsession import LMNSession

@dataclass
class LMNUser:
    cn: str
    displayName: str
    distinguishedName: str
    givenName: str
    homeDirectory: str
    homeDrive: str
    mail: list
    memberOf: list
    name: str
    proxyAddresses: list
    sAMAccountName: str
    sAMAccountType: str
    sn: str
    sophomorixAdminClass: str
    sophomorixAdminFile: str
    sophomorixBirthdate: str
    sophomorixCloudQuotaCalculated: list
    sophomorixComment: str
    sophomorixCreationDate: str # datetime
    sophomorixCustom1: str
    sophomorixCustom2: str
    sophomorixCustom3: str
    sophomorixCustom4: str
    sophomorixCustom5: str
    sophomorixCustomMulti1: list
    sophomorixCustomMulti2: list
    sophomorixCustomMulti3: list
    sophomorixCustomMulti4: list
    sophomorixCustomMulti5: list
    sophomorixDeactivationDate: str # datetime
    sophomorixExamMode: list
    sophomorixExitAdminClass: str
    sophomorixFirstnameASCII: str
    sophomorixFirstnameInitial: str
    sophomorixFirstPassword: str
    sophomorixIntrinsic2: list
    sophomorixMailQuotaCalculated: list
    sophomorixMailQuota: list
    sophomorixQuota: list
    sophomorixRole: str
    sophomorixSchoolname: str
    sophomorixSchoolPrefix: str
    sophomorixSessions: List[LMNSession]
    sophomorixStatus: str
    sophomorixSurnameASCII: str
    sophomorixSurnameInitial: str
    sophomorixTolerationDate: str # datetime
    sophomorixUnid: str
    sophomorixUserToken: str
    sophomorixWebuiDashboard: list
    sophomorixWebuiPermissionsCalculated: list
    unixHomeDirectory: str
    internet: bool = field(init=False)
    intranet: bool = field(init=False)
    printing: bool = field(init=False)
    webfilter: bool = field(init=False)
    wifi: bool = field(init=False)
    projects: list = field(init=False)
    schoolclasses: list = field(init=False)
    dn: str = field(init=False)
    permissions: list = field(init=False)

    def split_dn(self, dn):
        # 'CN=11c,OU=11c,OU=Students,OU=default-school,OU=SCHOOLS...' becomes :
        # [['CN', '11c'], ['OU', '11c'], ['OU', 'Students'],...]
        return [node.split("=") for node in dn.split(',')]

    def common_name(self, dn):
        try:
            # [['CN', '11c'], ['OU', '11c'], ['OU', 'Students'],...]
            return self.split_dn(dn)[0][1]
        except KeyError:
            return ''

    @staticmethod
    def _check_schoolclass_number(s):
        n = re.findall(r'\d+', s)
        if n:
            return int(n[0])
        else:
            return 10**10 # just a big number

    def extract_schoolclasses(self, membership):
        schoolclasses = []
        for dn in membership:
            if 'OU=Students' in dn:
                schoolclass = self.common_name(dn)
                if schoolclass:
                    schoolclasses.append(schoolclass)
        schoolclasses = sorted(schoolclasses, key=lambda s: (self._check_schoolclass_number(s), s))
        return schoolclasses

    def extract_projects(self, membership):
        projects = []
        for dn in membership:
            if 'OU=Projects' in dn:
                project = self.common_name(dn)
                if project:
                    projects.append(project)
        projects.sort()
        return projects

    def extract_management(self):
        for group in ['internet', 'intranet', 'printing', 'webfilter', 'wifi']:
            setattr(self, group, False)
            for dn in self.memberOf:
                if dn.startswith(f"CN={group},OU=Management"):
                    setattr(self, group, True)

    def parse_permissions(self):
        self.permissions = {}

        for perm in self.sophomorixWebuiPermissionsCalculated:
            module, value = perm.split(': ')
            self.permissions[module] = value == 'true'

    def __post_init__(self):
        self.schoolclasses = self.extract_schoolclasses(self.memberOf)
        self.projects = self.extract_projects(self.memberOf)
        self.dn = self.distinguishedName
        self.extract_management()
        self.parse_permissions()

