# 适配最新的魔方验证，可以自动识别，暂未做手动验证，但是只支持腾讯和阿里的服务器，其他服务器可用腾讯阿里的代理，源码暂不放出来，放出来估计又凉了
# 还有一些小bug，有大佬可以把他改进一下，暂时没空写
# MadRabbit
Nvjdc的前端和部分功能，主要镜像小，配置要求不高，可用配套的代理池，不用当心代理问题

# 配置:
1、新建一个项目
```
mkdir -p  Rabbit && cd Rabbit
```
2、创建一个目录放配置
```
mkdir -p  Config && cd Config
```
3、下载config.json 配置文件 并且修改自己的配置 不能缺少
```
wget -O Config.json  https://raw.githubusercontent.com/ht944/MadRabbit/main/Config.json
```
国内用
```
wget -O Config.json  https://ghproxy.com/https://raw.githubusercontent.com/ht944/MadRabbit/main/Config.json
```
4、配置完后
```
cd ..
```

# 安装和启动：
## 使用我的镜像
```
docker pull ht944/rabbit:latest
```
### 启动
```
docker run --name rabbit -d  -v "$(pwd)"/Config:/usr/src/Project/Config -p 5701:1234 ht944/rabbit:latest
```
# 第一次启动时会下载浏览器，可能比较慢
### 使用稳定的代理，不能有账号密码（支持socks，http代理）
格式：http://xxx.xxx.xxx.xxx:xxxx 或 socks://xxx.xxx.xxx.xxx:xxxx
设置配置文件中的proxy即可

# 强调一遍
## 配置文件修改后，重新启动容器

## 特别声明:

* 本仓库涉仅用于测试和学习研究，禁止用于商业用途，不能保证其合法性，准确性，完整性和有效性，请根据情况自行判断.

* 本项目内所有资源文件，禁止任何公众号、自媒体进行任何形式的转载、发布。

* ht944对任何代码问题概不负责，包括但不限于由任何脚本错误导致的任何损失或损害.

* 间接使用本仓库搭建的任何用户，包括但不限于建立VPS或在某些行为违反国家/地区法律或相关法规的情况下进行传播, ht944对于由此引起的任何隐私泄漏或其他后果概不负责.

* 请勿将本项目的任何内容用于商业或非法目的，否则后果自负.

* 如果任何单位或个人认为该项目的脚本可能涉嫌侵犯其权利，则应及时通知并提供身份证明，所有权证明，我们将在收到认证文件后删除相关代码.

* 任何以任何方式查看此项目的人或直接或间接使用本仓库项目的任何脚本的使用者都应仔细阅读此声明。ht944 保留随时更改或补充此免责声明的权利。一旦使用并复制了任何本仓库项目的规则，则视为您已接受此免责声明.

**您必须在下载后的24小时内从计算机或手机中完全删除以上内容.**  </br>
> ***您使用或者复制了本仓库且本人制作的任何脚本，则视为`已接受`此声明，请仔细阅读***

## 多谢
