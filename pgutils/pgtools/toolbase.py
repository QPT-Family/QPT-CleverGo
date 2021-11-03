
class ToolBase:
    """pygame工具基类，所有自定义工具均需继承ToolBase"""
    def __init__(self):
        # 工具是否被激活
        self.active = False

    def enable(self):
        """激活工具"""
        self.active = True

    def disable(self):
        """冻结工具"""
        self.active = False

    def update(self):
        """
        对工具状态进行更新

        所有工具类均需重写该方法
        """
        raise NotImplementedError
