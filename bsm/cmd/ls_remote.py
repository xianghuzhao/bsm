from bsm.cmd.base import Base

class LsRemote(Base):
    def execute(self):
        return self._bsm.ls_remote()
