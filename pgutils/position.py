import pygame
from typing import Union, List, Tuple


def pos_in_surface(pos: Union[List[int or float], Tuple[int or float]],
                   surface: pygame.Surface) -> bool:
    """判断pos位置是否在pygame.surface范围内"""
    offset = surface.get_abs_offset()
    surface_size = surface.get_size()
    if offset[0] < pos[0] < (offset[0] + surface_size[0]) and \
            offset[1] < pos[1] < (offset[1] + surface_size[1]):
        return True
    else:
        return False
