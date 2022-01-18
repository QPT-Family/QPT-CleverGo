# 机巧围棋(CleverGo)项目总览及介绍

## 1. 项目简介

2016年3月，阿尔法狗以4:1战胜围棋世界冠军李世石。自此开始，深度强化学习受到空前的关注并成为AI领域的研究热点，彻底引爆了以深度学习为核心技术的第三次人工智能热潮。

机巧围棋利用Python+Pygame+PaddlePaddle基于AlphaGo Zero算法打造了一款点击按钮就能可视化的训练9路围棋人工智能的程序，并搭建了一整套简单易用的围棋AI学习、开发、训练及效果可视化验证框架。

机巧围棋项目源码及技术原理文档全部免费开源，真诚期望您能够在GitHub上点个**Star**支持机巧围棋鸭~

**项目GitHub仓库地址**：[https://github.com/QPT-Family/QPT-CleverGo](https://github.com/QPT-Family/QPT-CleverGo)

**QQ群**：935098082



## 2. 开发者简介

机巧围棋项目归属于GitHub组织QPT软件包家族(QPT Family)，由DeepGeGe和GT-Zhang共同开发并维护。

- QPT Family主页：[https://github.com/QPT-Family](https://github.com/QPT-Family)
- QPT Family官方交流群：935098082

DeepGeGe：QPT Family成员

- CSDN博客：[https://blog.csdn.net/qq_24178985](https://blog.csdn.net/qq_24178985)
- GitHub主页：[https://github.com/DeepGeGe](https://github.com/DeepGeGe)

GT-Zhang：QPT Family创始人

- GitHub主页：[https://github.com/GT-ZhangAcer](https://github.com/GT-ZhangAcer)



## 3. 效果展示

机巧围棋程序界面：

![1_1](https://github.com/QPT-Family/QPT-CleverGo/blob/main/pictures/1_1.png)

效果展示视频链接：[https://www.bilibili.com/video/BV1N3411C742?spm_id_from=333.999.0.0](https://www.bilibili.com/video/BV1N3411C742?spm_id_from=333.999.0.0)



## 4. 技术原理文档目录

机巧围棋技术原理文档主要讲解项目相关知识、算法原理及程序逻辑，具体目录如下：

1. 机巧围棋(CleverGo)项目总览及介绍
2. 围棋基本知识
3. 围棋程序逻辑
4. 游戏开发引擎(Pygame)核心方法
5. 深度学习框架(PaddlePaddle)使用教程
6. 深度强化学习基本知识
7. 阿尔法狗(AlphaGo)算法原理

8. 机巧围棋(CleverGo)程序设计
9. 机巧围棋(CleverGo)远景规划
10. 机巧围棋(CleverGo)项目总结



## 5. 开发者说

**DeepGeGe**：2016年，阿尔法狗横空出世，使我深深地感受到了围棋和人工智能的魅力。自此开始，我自学围棋和人工智能，成为了AI算法工程师。围棋人工智能前有阿尔法狗，后有大名鼎鼎的绝艺，但是他们都离我们非常遥远，就像天上的星星。当了解阿尔法狗算法原理之后，我就在想是不是能够训练出一个属于我自己的阿尔法狗，或者说能不能做出一款不需要任何人工智能领域专业知识，只需点击一个按钮就能训练一个阿尔法狗？

机巧围棋从2021年3月6日开始开发，直至4月底，各大功能模块基本完成。5-8月项目搁置。9月初，我找到GT-Zhang大佬商定一起合作开发并维护机巧围棋项目。从9月底到10月中旬，重构了整个项目，并完成了和优化全部核心功能。

机巧围棋不需要任何专业背景知识，只需要点击按钮就能够体验训练属于自己的围棋人工智能阿尔法狗，核心理念是：Easy AI for Everyone! 

期望大家能够去GitHub上给机巧围棋点个**Star**鸭~



## 6. 致谢

1. 机巧围棋界面设计参考了HapHac作者的weiqi项目，采用了该项目的部分素材，但是围棋程序逻辑及游戏引擎与该项目不同。

   参考项目地址：[https://github.com/HapHac/weiqi](https://github.com/HapHac/weiqi)

2. 机巧围棋中围棋程序内核采用了aigagror作者的GymGo项目，机巧围棋模拟器环境在该项目的基础上进行了自定义封装。此外，机巧围棋项目开发者DeepGeGe（鸽鸽）也是GymGo项目的Contributor~

   参考项目地址：[https://github.com/aigagror/GymGo](https://github.com/aigagror/GymGo)

3. 机巧围棋技术原理文档中，深度强化学习基本知识及阿尔法狗算法原理部分参考了wangshusen作者的DRL项目。综合该项目中相关深度强化学习知识，讲解了零狗算法在机巧围棋中的应用。

   参考项目地址：[https://github.com/wangshusen/DRL](https://github.com/wangshusen/DRL)

4. 机巧围棋中，有关蒙特卡洛树搜索等部分参考了junxiaosong作者的AlphaZero_Gomoku项目。其中蒙特卡洛树搜索的实现方式基本与该项目中实现保持一致，并结合机巧围棋中相关功能需求进行了部分更改。

   参考项目地址：[https://github.com/junxiaosong/AlphaZero_Gomoku](https://github.com/junxiaosong/AlphaZero_Gomoku)
