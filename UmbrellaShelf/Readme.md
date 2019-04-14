# 雨伞租赁系统硬件部分

[TOC]

## 路由器配置

- 在路由器插电之后，先进入后台管理界面（http://192.168.1.1），登陆密码：`mercury`
- 路由器名称密码皆为`umbrella`，勿作修改
- 在后台管理页面将电脑IP地址和MAC地址绑定，设置IP地址为`192.168.1.100`，保证伞扣通过WiFi连接电脑时是固定的IP地址

## 伞架和伞扣的配置

- 在保证服务器启动和路由器正常配置的情况下，直接插电即可
- 硬件采用NodeMCU（芯片型号：ESP-12）

## 硬件编程环境的搭建

- 先到Arduino官网（https://www.arduino.cc/en/Main/Software）下载IDE
- 打开Arduino IDE，选择`文件` -> `首选项` ，在`附加开发板管理器`中填入`http://arduino.esp8266.com/stable/package_esp8266com_index.json`
- `工具` -> `管理库`安装`MFRC522`、`ArduinoJson`库
- `工具` -> `开发板` -> `开发板管理器`，下载`ESP8266`开发板
- 打开`umbrella.ino`文件，选择开发板为`NodeMCU1.0`，选择正确端口即可编译上传

### 参考库

- ESP8266WiFi库：主要用于TCP协议控制。不用单独安装，下载ESP8266开发板之后自带。参考资料：https://arduino-esp8266.readthedocs.io/en/latest/esp8266wifi/readme.html
- ArduinoJson库：主要用于JSON格式数据的构建