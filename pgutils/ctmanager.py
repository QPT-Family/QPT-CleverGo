# -*- coding: utf-8 -*-
# @Time    : 2021/10/7 10:57
# @Author  : He Ruizhi
# @File    : ctmanager.py
# @Software: PyCharm

from pgutils.pgcontrols.ctbase import CtBase
import pygame
from typing import List


class CtManager:
    def __init__(self):
        self.controls = []

    def register(self, controls: List[CtBase]) -> None:
        """
        控件注册

        :param controls: pygame控件
        :return:
        """
        for control in controls:
            self.controls.append(control)
        return None

    def update(self, event: pygame.event) -> None:
        """
        对所有注册的激活控件进行更新

        :param event: pygame事件
        :return:
        """
        for control in self.controls:
            if control.active:
                control.update(event)
        return None
