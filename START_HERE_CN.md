# 从零开始发布到 Docker Hub

这个项目会发布一个真实可运行的工具，而不是只放一段广告。它会检查 PCB 文件包中是否包含常见的 Gerber、钻孔、板框、BOM 和坐标文件，并在说明页中自然链接到 PCBCool。

## 文件说明

- `pcb_file_checker.py`：工具主体
- `Dockerfile`：告诉 Docker 如何打包工具
- `README.md`：Docker Hub 仓库的完整英文介绍
- `DOCKER_HUB_CONTENT.md`：账号资料与仓库字段
- `publish-to-docker-hub.ps1`：Windows 一键构建、测试和发布脚本
- `sample-gerber`：用于测试的示例文件包
- `LICENSE`：MIT 开源许可证

## 1. 注册 Docker Hub

建议优先尝试 Docker ID：

```text
lokizhan
```

如已被占用，可使用：

```text
lokizhanpcb
```

Docker ID 一旦创建后不可修改，因此不要随意使用临时名称。

## 2. 安装并启动 Docker Desktop

在 Windows 上安装 Docker Desktop。安装后启动软件，等待左下角或主界面显示 Docker Engine 正常运行。

打开 PowerShell，执行：

```powershell
docker version
```

如果能显示 Client 和 Server 信息，说明安装成功。

## 3. 创建 Docker Hub 仓库

登录 Docker Hub 后：

1. 进入 `My Hub`。
2. 选择 `Repositories`。
3. 点击 `Create repository`。
4. Namespace 选择自己的 Docker ID。
5. Repository name 填写 `pcb-file-checker`。
6. Short description 填写：

```text
Lightweight checker for Gerber, drill, BOM, and pick-and-place files.
```

7. Visibility 选择 `Public`。
8. 点击 `Create`。

## 4. 解压项目

将 ZIP 解压到一个容易找到的位置，例如：

```text
D:\Docker\pcbcool-pcb-file-checker
```

打开这个文件夹，在资源管理器地址栏输入：

```text
powershell
```

按 Enter，即可在当前文件夹打开 PowerShell。

## 5. 最简单的发布方式

确认最终 Docker ID。若使用 `lokizhan`，执行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\publish-to-docker-hub.ps1 -DockerUsername lokizhan
```

脚本会自动完成：

1. 检查 Docker 是否正常运行
2. 打开 Docker Hub 登录流程
3. 构建 `1.0.0` 和 `latest` 两个标签
4. 用示例 PCB 文件测试工具
5. 上传两个标签到 Docker Hub

若你的 Docker ID 不是 `lokizhan`，将命令最后的用户名替换为实际 ID。

## 6. 手动命令方式

也可以逐条执行：

```powershell
docker login
docker build -t lokizhan/pcb-file-checker:1.0.0 -t lokizhan/pcb-file-checker:latest .
$samplePath = (Resolve-Path ".\sample-gerber").Path
docker run --rm -v "${samplePath}:/data:ro" lokizhan/pcb-file-checker:1.0.0 /data --assembly
docker push lokizhan/pcb-file-checker:1.0.0
docker push lokizhan/pcb-file-checker:latest
```

## 7. 添加仓库介绍和 PCBCool 链接

上传成功后回到 Docker Hub：

1. 进入 `My Hub > Repositories`。
2. 打开 `pcb-file-checker`。
3. 在 `Repository overview` 下点击 `Add overview` 或 `Edit`。
4. 打开本项目的 `README.md`。
5. 复制全部内容并粘贴到 Overview 编辑器。
6. 点击 `Preview` 检查格式。
7. 点击 `Update`。

README 底部已经包含两个自然链接：

- PCBCool 官网
- PCBCool 在线 PCB 报价系统

不要再额外堆叠“best PCB manufacturer”等关键词锚文本。

## 8. 最终测试公开镜像

在 PowerShell 中执行：

```powershell
docker pull lokizhan/pcb-file-checker:latest
```

然后用任意 PCB 文件夹测试：

```powershell
$pcbFiles = "D:\PCB-Files\Your-Gerber-Folder"
docker run --rm -v "${pcbFiles}:/data:ro" lokizhan/pcb-file-checker:latest
```

需要同时检查 BOM 和坐标文件时：

```powershell
docker run --rm -v "${pcbFiles}:/data:ro" lokizhan/pcb-file-checker:latest /data --assembly
```

## 9. 发布后应看到的页面信息

```text
lokizhan/pcb-file-checker
```

页面应显示：

- `latest` 标签
- `1.0.0` 标签
- 完整 Overview
- PCBCool 品牌链接
- Pull command

## 10. 后续维护

以后修改代码后，将版本号改为 `1.0.1`：

```powershell
.\publish-to-docker-hub.ps1 -DockerUsername lokizhan -Version 1.0.1
```

不要删除旧版标签。保留历史版本更符合正常软件项目的维护方式。
