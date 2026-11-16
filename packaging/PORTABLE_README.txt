Local Face Lab / 本地表情实验室 — 独立运行包

Linux x86_64：解压整个目录后，双击 LocalFaceLab 可执行文件，或在终端执行 ./LocalFaceLab。
程序会自动打开本机浏览器；点击“开启摄像头”并允许摄像头权限。

包内已包含 Python、运行依赖和全部所需模型，不需要安装 Python、pip 或首次联网下载模型。
不要只复制单个可执行文件；必须保留同目录下的 _internal 文件夹。

默认地址：http://127.0.0.1:8766
关闭终端或按 Ctrl+C 停止服务。再次启动会打开已经运行的本软件。
录像保存在 ~/.local/share/local-face-lab/recordings/，不会保存在临时目录。

支持范围：Linux x86_64，glibc 2.35 或以上（例如 Ubuntu 22.04 及更新版本）。
需要操作系统已有正常工作的摄像头驱动和现代浏览器。
本包不是 Windows、macOS 或 RK3568/ARM 程序。

自检：./LocalFaceLab --self-test
只启动服务：./LocalFaceLab --no-browser
更换端口：./LocalFaceLab --port 8767

仅用于学习和非商业研究。第三方许可见 _internal/licenses 和 _internal/face_lab/resources/licenses。
软件不读取内心、不测谎、不诊断心理状态，也不是经过验证的微表情识别系统。
