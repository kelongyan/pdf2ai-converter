#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 转 Markdown 交互式启动器"""

import sys
import os
from pathlib import Path
from tkinter import Tk, filedialog
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box
from config_manager import ConfigManager
import subprocess

# 设置 Windows 控制台 UTF-8 编码
if sys.platform == "win32":
    os.system("chcp 65001 > nul")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

console = Console(force_terminal=True, legacy_windows=False)


class PDFConverter:
    """PDF 转换工具启动器（支持 Markdown 和 Word）"""

    def __init__(self):
        self.config_manager = ConfigManager()
        self.current_profile = None

    def show_banner(self):
        """显示欢迎横幅"""
        banner = """
[bold cyan]╔══════════════════════════════════════════════════════════╗
║          🚀 PDF 转换工具 v2.1                           ║
║          支持 Markdown 和 Word 格式                      ║
╚══════════════════════════════════════════════════════════╝[/bold cyan]
        """
        console.print(banner)

    def show_current_config(self):
        """显示当前配置"""
        if self.current_profile:
            table = Table(show_header=False, box=box.SIMPLE)
            table.add_column("项目", style="cyan")
            table.add_column("值", style="green")

            table.add_row("📋 配置名称", self.current_profile.get("name", "未命名"))
            table.add_row("🤖 模型", self.current_profile["model"])
            table.add_row("📐 分辨率", str(self.current_profile.get("dpi", 150)))
            table.add_row("📦 分段大小", str(self.current_profile.get("chunk_size", 10)))
            table.add_row("✅ 状态", "已连接")

            console.print(Panel(table, title="[bold]当前配置[/bold]", border_style="green"))
        else:
            console.print("[yellow]⚠️  未加载配置[/yellow]\n")

    def create_new_config(self):
        """创建新配置"""
        console.print("\n[bold cyan]📝 创建新配置[/bold cyan]\n")

        name = Prompt.ask("配置名称", default="default")
        api_url = Prompt.ask("API URL", default="https://api.openai.com/v1")
        api_key = Prompt.ask("API Key")
        model = Prompt.ask("模型 ID", default="gpt-4o")

        console.print("\n[bold]⚙️  高级选项[/bold]")
        dpi = int(Prompt.ask("分辨率 DPI", default="150"))
        chunk_size = int(Prompt.ask("分段大小（每次处理页数）", default="10"))

        # 保存配置
        self.config_manager.save_profile(
            name=name,
            api_url=api_url,
            api_key=api_key,
            model=model,
            dpi=dpi,
            chunk_size=chunk_size,
        )

        self.current_profile = self.config_manager.get_profile(name)
        self.current_profile["name"] = name

        console.print(f"\n[green]✅ 配置 '{name}' 已保存[/green]\n")

    def load_config(self):
        """加载配置"""
        profiles = self.config_manager.list_profiles()

        if not profiles:
            console.print("[yellow]⚠️  未找到已保存的配置[/yellow]")
            if Confirm.ask("是否创建新配置？", default=True):
                self.create_new_config()
            return

        console.print("\n[bold cyan]📋 已保存的配置：[/bold cyan]\n")
        for i, name in enumerate(profiles, 1):
            profile = self.config_manager.get_profile(name)
            console.print(f"  [{i}] {name} - {profile['model']}")

        console.print(f"  [0] 创建新配置\n")

        choice = Prompt.ask("选择配置", choices=[str(i) for i in range(len(profiles) + 1)])

        if choice == "0":
            self.create_new_config()
        else:
            name = profiles[int(choice) - 1]
            self.current_profile = self.config_manager.get_profile(name)
            self.current_profile["name"] = name
            console.print(f"\n[green]✅ 已加载配置 '{name}'[/green]\n")

    def select_pdf_file(self) -> str:
        """选择 PDF 文件"""
        console.print("\n[cyan]📁 正在打开文件选择器...[/cyan]")

        # 隐藏 tkinter 主窗口
        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        file_path = filedialog.askopenfilename(
            title="选择 PDF 文件",
            filetypes=[("PDF 文件", "*.pdf"), ("所有文件", "*.*")],
        )

        root.destroy()

        if file_path:
            console.print(f"[green]✅ 已选择：{file_path}[/green]\n")
            return file_path
        else:
            console.print("[yellow]⚠️  未选择文件[/yellow]\n")
            return None

    def select_pdf_folder(self) -> str:
        """选择文件夹（批量处理）"""
        console.print("\n[cyan]📁 正在打开文件夹选择器...[/cyan]")

        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        folder_path = filedialog.askdirectory(title="选择包含 PDF 的文件夹")

        root.destroy()

        if folder_path:
            pdf_files = list(Path(folder_path).glob("*.pdf"))
            console.print(f"[green]✅ 找到 {len(pdf_files)} 个 PDF 文件[/green]\n")
            return folder_path
        else:
            console.print("[yellow]⚠️  未选择文件夹[/yellow]\n")
            return None

    def update_config_file(self):
        """更新 config.yaml"""
        import yaml

        config = {
            "model": {
                "type": "openai_compatible",
                "name": self.current_profile["model"],
                "api_key": self.current_profile["api_key"],
                "base_url": self.current_profile["api_url"],
            },
            "pdf": {"dpi": self.current_profile.get("dpi", 150)},
            "chunk_size": self.current_profile.get("chunk_size", 10),
            "quality_check": True,
            "output": {"cleanup_images": True, "add_page_separator": True},
        }

        with open("config.yaml", "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True)

    def process_file(self, pdf_path: str, output_format: str = "markdown"):
        """处理单个文件

        Args:
            pdf_path: PDF 文件路径
            output_format: 输出格式 ("markdown" 或 "word")
        """
        console.print(f"\n[bold green]🚀 开始处理：{Path(pdf_path).name}[/bold green]\n")

        # 更新配置文件
        self.update_config_file()

        # 调用对应的处理程序
        venv_python = Path("venv/Scripts/python.exe")
        if not venv_python.exists():
            venv_python = Path("venv/bin/python")  # Linux/Mac

        if output_format == "word":
            # 询问转换模式
            console.print("\n[bold]选择转换模式：[/bold]")
            console.print("  [1] 快速模式 - 只保留内容结构（速度快，成本低）")
            console.print("  [2] 精确模式 - 保留样式格式（速度慢，成本高）\n")

            mode_choice = Prompt.ask("请选择", choices=["1", "2"], default="2")
            mode = "fast" if mode_choice == "1" else "precise"

            cmd = [str(venv_python), "main_word.py", pdf_path, "", mode]
        else:
            cmd = [str(venv_python), "main.py", pdf_path]

        try:
            subprocess.run(cmd, check=True)
            console.print("\n[bold green]✅ 处理完成！[/bold green]\n")
        except subprocess.CalledProcessError as e:
            console.print(f"\n[bold red]❌ 处理失败：{e}[/bold red]\n")

    def process_folder(self, folder_path: str, output_format: str = "markdown"):
        """批量处理文件夹

        Args:
            folder_path: 文件夹路径
            output_format: 输出格式 ("markdown" 或 "word")
        """
        pdf_files = list(Path(folder_path).glob("*.pdf"))

        if not pdf_files:
            console.print("[yellow]⚠️  文件夹中没有 PDF 文件[/yellow]\n")
            return

        console.print(f"\n[bold cyan]📦 批量处理模式[/bold cyan]")
        console.print(f"找到 {len(pdf_files)} 个文件\n")

        for i, pdf_file in enumerate(pdf_files, 1):
            console.print(f"[cyan]━━━ 处理 {i}/{len(pdf_files)} ━━━[/cyan]")
            self.process_file(str(pdf_file), output_format)

        console.print("[bold green]✅ 批量处理完成！[/bold green]\n")

    def show_menu(self):
        """显示主菜单"""
        while True:
            self.show_current_config()

            console.print("[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]\n")

            menu = Table(show_header=False, box=None, padding=(0, 2))
            menu.add_column(style="bold cyan")
            menu.add_column(style="white")

            menu.add_row("[1]", "📝 转换为 Markdown（单个文件）")
            menu.add_row("[2]", "📄 转换为 Word（单个文件）")
            menu.add_row("[3]", "📁 批量转换为 Markdown")
            menu.add_row("[4]", "📁 批量转换为 Word")
            menu.add_row("[5]", "⚙️  配置管理")
            menu.add_row("[6]", "🔧 编辑当前配置")
            menu.add_row("[0]", "👋 退出")

            console.print(menu)
            console.print("\n[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]\n")

            choice = Prompt.ask("请选择", choices=["0", "1", "2", "3", "4", "5", "6"])

            if choice == "0":
                console.print("\n[cyan]👋 再见！[/cyan]\n")
                break
            elif choice == "1":
                if not self.current_profile:
                    console.print("[yellow]⚠️  请先加载或创建配置[/yellow]\n")
                    continue
                pdf_path = self.select_pdf_file()
                if pdf_path:
                    self.process_file(pdf_path, "markdown")
            elif choice == "2":
                if not self.current_profile:
                    console.print("[yellow]⚠️  请先加载或创建配置[/yellow]\n")
                    continue
                pdf_path = self.select_pdf_file()
                if pdf_path:
                    self.process_file(pdf_path, "word")
            elif choice == "3":
                if not self.current_profile:
                    console.print("[yellow]⚠️  请先加载或创建配置[/yellow]\n")
                    continue
                folder_path = self.select_pdf_folder()
                if folder_path:
                    self.process_folder(folder_path, "markdown")
            elif choice == "4":
                if not self.current_profile:
                    console.print("[yellow]⚠️  请先加载或创建配置[/yellow]\n")
                    continue
                folder_path = self.select_pdf_folder()
                if folder_path:
                    self.process_folder(folder_path, "word")
            elif choice == "5":
                self.load_config()
            elif choice == "6":
                if self.current_profile:
                    self.edit_current_config()
                else:
                    console.print("[yellow]⚠️  请先加载配置[/yellow]\n")

    def edit_current_config(self):
        """编辑当前配置"""
        console.print("\n[bold cyan]🔧 编辑配置[/bold cyan]\n")

        name = self.current_profile["name"]
        api_url = Prompt.ask("API URL", default=self.current_profile["api_url"])
        api_key = Prompt.ask(
            "API Key (留空保持不变)", default="", show_default=False
        )
        if not api_key:
            api_key = self.current_profile["api_key"]

        model = Prompt.ask("模型 ID", default=self.current_profile["model"])
        dpi = int(Prompt.ask("分辨率 DPI", default=str(self.current_profile.get("dpi", 150))))
        chunk_size = int(
            Prompt.ask("分段大小", default=str(self.current_profile.get("chunk_size", 10)))
        )

        # 保存配置
        self.config_manager.save_profile(
            name=name,
            api_url=api_url,
            api_key=api_key,
            model=model,
            dpi=dpi,
            chunk_size=chunk_size,
        )

        self.current_profile = self.config_manager.get_profile(name)
        self.current_profile["name"] = name

        console.print(f"\n[green]✅ 配置已更新[/green]\n")

    def run(self):
        """运行启动器"""
        self.show_banner()

        # 尝试加载上次使用的配置
        last_profile = self.config_manager.get_last_profile()
        if last_profile:
            profiles = self.config_manager.list_profiles()
            last_name = self.config_manager.config.get("last_used")
            self.current_profile = last_profile
            self.current_profile["name"] = last_name
            console.print(f"[green]✅ 已自动加载上次配置：{last_name}[/green]\n")
        else:
            console.print("[yellow]⚠️  首次使用，请创建配置[/yellow]\n")
            self.create_new_config()

        # 显示主菜单
        self.show_menu()


if __name__ == "__main__":
    try:
        converter = PDFConverter()
        converter.run()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️  用户中断[/yellow]\n")
    except Exception as e:
        console.print(f"\n[bold red]❌ 错误：{e}[/bold red]\n")
        import traceback
        traceback.print_exc()
