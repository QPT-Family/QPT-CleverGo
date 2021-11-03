# -*- coding: utf-8 -*-
# @Time    : 2021/10/7 10:57
# @Author  : He Ruizhi
# @File    : manager.py
# @Software: PyCharm

from pgutils.pgcontrols.ctbase import CtBase
from pgutils.pgtools.toolbase import ToolBase
import pygame
from typing import List, Union


class Manager:
    def __init__(self):
        self.controls = []
        self.tools = []

    def control_register(self, controls: Union[List[CtBase], CtBase]):
        """
        控件注册

        :param controls: pygame控件或控件数组
        :return:
        """
        if isinstance(controls, CtBase):
            self.controls.append(controls)
        else:
            for control in controls:
                self.controls.append(control)

    def tool_register(self, tools: Union[List[ToolBase], ToolBase]):
        """
        工具注册

        :param tools: pygame工具或工具数组
        :return:
        """
        if isinstance(tools, ToolBase):
            self.tools.append(tools)
        else:
            for tool in tools:
                self.tools.append(tool)

    def control_update(self, event: pygame.event):
        """
        对所有注册的激活控件进行更新

        :param event: pygame事件
        :return:
        """
        for control in self.controls:
            if control.active:
                control.update(event)

    def tool_update(self):
        """对所有激活的工具进行更新"""
        for tool in self.tools:
            if tool.active:
                tool.update()
                # pgtool会在更新后冻结
                tool.disable()
