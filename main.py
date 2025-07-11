import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import requests
import json
import os
import base64
from datetime import datetime
import threading
import webbrowser

class GitHubManager:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub 仓库管理工具")
        self.root.geometry("1000x700")
        self.root.minsize(800, 500)
        
        # 设置字体
        self.default_font = ('Microsoft YaHei UI', 10)
        
        # 配置文件路径
        self.config_file = os.path.expanduser("~/.github_manager_config.json")
        
        # 数据
        self.github_token = tk.StringVar()
        self.selected_token_id = None
        self.repos = []
        self.tokens = self._load_tokens()
        
        # 创建界面
        self._create_widgets()
        
    def _create_widgets(self):

        # 主框架
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Token管理区域
        token_frame = ttk.LabelFrame(main_frame, text="GitHub Token 管理", padding=10)
        token_frame.grid(row=0, column=0, columnspan=2, sticky=tk.EW, pady=5)
        
        # Token列表
        ttk.Label(token_frame, text="已保存的 Token:", font=self.default_font).grid(row=0, column=0, sticky=tk.W)
        self.token_listbox = tk.Listbox(token_frame, width=60, height=5, font=self.default_font)
        self.token_listbox.grid(row=1, column=0, sticky=tk.EW, pady=5)
        self._refresh_token_list()
        
        # Token操作按钮
        token_btn_frame = ttk.Frame(token_frame)
        token_btn_frame.grid(row=1, column=1, sticky=tk.NS, padx=5)
        
        ttk.Button(token_btn_frame, text="网页获取 Token", command=self._web_token).pack(fill=tk.X, pady=2)
        ttk.Button(token_btn_frame, text="添加 Token", command=self._add_token).pack(fill=tk.X, pady=2)
        ttk.Button(token_btn_frame, text="编辑 Token", command=self._edit_token).pack(fill=tk.X, pady=2)
        ttk.Button(token_btn_frame, text="删除 Token", command=self._delete_token).pack(fill=tk.X, pady=2)
        ttk.Button(token_btn_frame, text="使用选中 Token",  command=self._use_selected_token).pack(fill=tk.X, pady=2)
        
        # 当前使用的Token
        ttk.Label(token_frame, text="当前使用的 Token:", font=self.default_font).grid(row=2, column=0, sticky=tk.W)
        self.current_token_label = ttk.Label(token_frame, text="未选择 Token", foreground="red", font=self.default_font)
        self.current_token_label.grid(row=2, column=1, sticky=tk.W)
        
        # 仓库操作区域
        repo_frame = ttk.LabelFrame(main_frame, text="仓库操作", padding=10)
        repo_frame.grid(row=1, column=0, sticky=tk.NSEW, pady=5)
        
        # 仓库列表
        ttk.Label(repo_frame, text="我的 GitHub 仓库:", font=self.default_font).grid(row=0, column=0, sticky=tk.W)
        
        # 搜索框
        search_frame = ttk.Frame(repo_frame)
        search_frame.grid(row=1, column=0, sticky=tk.EW, pady=5)
        
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var, width=30, font=self.default_font).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(search_frame, text="搜索", command=self._search_repos).pack(side=tk.LEFT, padx=5)
        
        # 仓库表格
        columns = ("name", "description", "updated_at", "visibility")
        self.repo_tree = ttk.Treeview(repo_frame, columns=columns, show="headings", height=15)
        self.repo_tree.bind("<Double-1>", self._show_repo_files)
        
        # 设置列标题
        self.repo_tree.heading("name", text="仓库名称")
        self.repo_tree.heading("description", text="描述")
        self.repo_tree.heading("updated_at", text="最后更新")
        self.repo_tree.heading("visibility", text="可见性")
        
        # 设置列宽
        self.repo_tree.column("name", width=150)
        self.repo_tree.column("description", width=300)
        self.repo_tree.column("updated_at", width=150)
        self.repo_tree.column("visibility", width=80)
        
        self.repo_tree.grid(row=2, column=0, sticky=tk.NSEW, pady=5)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(repo_frame, orient=tk.VERTICAL, command=self.repo_tree.yview)
        self.repo_tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=2, column=1, sticky=tk.NS)
        
        # 刷新按钮
        ttk.Button(repo_frame, text="刷新仓库列表", command=self._fetch_repos).grid(row=3, column=0, sticky=tk.W, pady=5)
        
        # 仓库操作按钮 - 第一行
        repo_btn_frame1 = ttk.Frame(repo_frame)
        repo_btn_frame1.grid(row=4, column=0, sticky=tk.EW, pady=2)
        
        ttk.Button(repo_btn_frame1, text="创建仓库", command=self._create_repo).pack(side=tk.LEFT, padx=5)
        ttk.Button(repo_btn_frame1, text="删除选中仓库", command=self._delete_repo).pack(side=tk.LEFT, padx=5)
        
        # 仓库操作按钮 - 第二行
        repo_btn_frame2 = ttk.Frame(repo_frame)
        repo_btn_frame2.grid(row=5, column=0, sticky=tk.EW, pady=2)
        
        ttk.Button(repo_btn_frame2, text="重命名选中仓库", command=self._rename_repo).pack(side=tk.LEFT, padx=5)
        ttk.Button(repo_btn_frame2, text="上传文件到选中仓库", command=self._upload_to_repo).pack(side=tk.LEFT, padx=5)
        ttk.Button(repo_btn_frame2, text="上传项目到选中仓库", command=self._upload_project_to_repo).pack(side=tk.LEFT, padx=5)
        ttk.Button(repo_btn_frame2, text="修改仓库可见性", command=self._change_repo_visibility).pack(side=tk.LEFT, padx=5)
        # 状态区域
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=5)
        
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(status_frame, textvariable=self.status_var, font=self.default_font).pack(side=tk.LEFT)
        
        # 设置权重，使界面可伸缩
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        repo_frame.columnconfigure(0, weight=1)
        repo_frame.rowconfigure(2, weight=1)

    #获取token
    def _web_token(self, event=None):
        url = 'https://github.com/settings/tokens'
        webbrowser.open(url)
    # 新增显示仓库文件列表的方法
    def _show_repo_files(self, event):
        selected_items = self.repo_tree.selection()
        if not selected_items:
            return
        
        repo_name = self.repo_tree.item(selected_items[0])['values'][0]
        username = self._get_username()
        if not username:
            return
        
        repo_full_name = f"{username}/{repo_name}"
        headers = self._get_headers()
        
        # 创建文件列表窗口
        file_list_window = tk.Toplevel(self.root)
        file_list_window.title(f"{repo_name} 文件列表")
        file_list_window.geometry("600x400")
        
        # 文件列表框
        file_listbox = tk.Listbox(file_list_window, width=80, height=20, font=self.default_font)
        file_listbox.pack(pady=10)
        
        # 选择框变量
        selected_files = []
        checkbuttons = []
        
        def select_file(file_path, var):
            if var.get() == 1:
                selected_files.append(file_path)
            else:
                if file_path in selected_files:
                    selected_files.remove(file_path)
        
        try:
            # 获取仓库中的文件列表
            url = f"https://api.github.com/repos/{repo_full_name}/contents"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                file_data = response.json()
                for file in file_data:
                    file_path = file['path']
                    var = tk.IntVar()
                    checkbutton = tk.Checkbutton(file_list_window, text=file_path, variable=var, command=lambda p=file_path, v=var: select_file(p, v))
                    checkbutton.pack(anchor=tk.W)
                    checkbuttons.append(checkbutton)
        except Exception as e:
            messagebox.showerror("错误", f"获取文件列表失败: {str(e)}")
        
        # 删除选中文件按钮
        def delete_selected_files():
            self._delete_files_from_repo(repo_name, selected_files)
            file_list_window.destroy()
        
        ttk.Button(file_list_window, text="删除选中文件", command=delete_selected_files).pack(pady=10)

    # 新增修改仓库可见性的方法
    def _change_repo_visibility(self):
        if not self.github_token.get():
            messagebox.showerror("错误", "请先选择一个Token")
            return
        
        # 获取选中的仓库
        selected_items = self.repo_tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请先选择一个仓库")
            return
        
        repo_name = self.repo_tree.item(selected_items[0])['values'][0]
        username = self._get_username()
        if not username:
            return
        
        repo_full_name = f"{username}/{repo_name}"
        
        # 创建修改可见性的窗口
        visibility_window = tk.Toplevel(self.root)
        visibility_window.title("修改仓库可见性")
        visibility_window.geometry("300x200")
        
        ttk.Label(visibility_window, text="选择新的可见性:", font=self.default_font).place(x=20, y=20)
        visibility_var = tk.StringVar(value="public")
        ttk.Radiobutton(visibility_window, text="公开", variable=visibility_var, value="public").place(x=100, y=20)
        ttk.Radiobutton(visibility_window, text="私有", variable=visibility_var, value="private").place(x=200, y=20)
        
        def update_visibility():
            new_visibility = visibility_var.get()
            private = new_visibility == "private"
            
            headers = self._get_headers()
            data = {"private": private}
            url = f"https://api.github.com/repos/{repo_full_name}"
            
            try:
                self.status_var.set(f"正在修改仓库 '{repo_name}' 的可见性...")
                self.root.update()
                
                response = requests.patch(url, headers=headers, json=data)
                
                if response.status_code == 200:
                    messagebox.showinfo("成功", f"仓库 '{repo_name}' 的可见性已修改为 {new_visibility}")
                    self._fetch_repos()  # 刷新仓库列表
                    visibility_window.destroy()
                else:
                    self._handle_api_error(response)
            except Exception as e:
                messagebox.showerror("错误", f"修改仓库可见性失败: {str(e)}")
            finally:
                self.status_var.set("就绪")
        
        ttk.Button(visibility_window, text="更新", command=update_visibility).place(x=100, y=150)
        ttk.Button(visibility_window, text="取消", command=visibility_window.destroy).place(x=200, y=150)


    # 删除仓库中文件的方法
    def _delete_files_from_repo(self, repo_name, selected_files):
        username = self._get_username()
        if not username:
            return
        
        repo_full_name = f"{username}/{repo_name}"
        headers = self._get_headers()
        
        for file_path in selected_files:
            url = f"https://api.github.com/repos/{repo_full_name}/contents/{file_path}"
            
            try:
                # 获取文件的 SHA 值
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    sha = response.json()['sha']
                    data = {
                        "message": f"Delete {file_path}",
                        "sha": sha
                    }
                    
                    # 发送删除请求
                    delete_response = requests.delete(url, headers=headers, json=data)
                    if delete_response.status_code != 200:
                        self._handle_api_error(delete_response)
            except Exception as e:
                messagebox.showerror("错误", f"删除文件 {file_path} 失败: {str(e)}")
        
        messagebox.showinfo("成功", f"已删除 {len(selected_files)} 个文件")
        self._fetch_repos()  # 刷新仓库列表
    
    def _load_tokens(self):
        """加载保存的Tokens"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('tokens', [])
            except Exception as e:
                messagebox.showerror("错误", f"加载配置文件失败: {str(e)}")
        return []
    
    def _save_tokens(self):
        """保存Tokens到配置文件"""
        try:
            data = {'tokens': self.tokens}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存配置文件失败: {str(e)}")
    
    def _refresh_token_list(self):
        """刷新Token列表"""
        self.token_listbox.delete(0, tk.END)
        for token in self.tokens:
            self.token_listbox.insert(tk.END, f"{token['id']}. {token['note']} ({token['created_at']})")
    
    def _add_token(self):
        """添加新Token"""
        

        token_window = tk.Toplevel(self.root)
        token_window.title("添加 GitHub Token")
        token_window.geometry("400x250")
        token_window.resizable(False, False)
        token_window.transient(self.root)
        token_window.grab_set()
        
        #小眼睛
        token_entry = ttk.Entry(token_window, width=40, show='*', font=self.default_font)
        token_entry.place(x=100, y=20)

        ttk.Label(token_window, text="Token:", font=self.default_font).place(x=20, y=20)
        token_entry = ttk.Entry(token_window, width=40, show='*', font=self.default_font)
        token_entry.place(x=100, y=20)
        
        ttk.Label(token_window, text="备注用途:", font=self.default_font).place(x=20, y=60)
        note_entry = ttk.Entry(token_window, width=40, font=self.default_font)
        note_entry.place(x=100, y=60)
        
        ttk.Label(token_window, text="Token权限说明:", font=self.default_font).place(x=20, y=100)
        perms_text = tk.Text(token_window, width=45, height=4, font=self.default_font)
        perms_text.place(x=20, y=120)
        perms_text.insert(tk.END, "需要repo权限(读写仓库)\nadmin:repo_hook权限(管理仓库钩子)")
        perms_text.config(state=tk.DISABLED)

        show_token_var = tk.IntVar()
        def toggle_token_visibility():
            if show_token_var.get() == 1:
                token_entry.config(show='')
            else:
                token_entry.config(show='*')

        show_token_checkbox = tk.Checkbutton(token_window, text="显示Token", variable=show_token_var, command=toggle_token_visibility)
        show_token_checkbox.place(x=320, y=20)
        
        def save_token():
            token = token_entry.get().strip()
            note = note_entry.get().strip()
            
            if not token:
                messagebox.showerror("错误", "Token不能为空")
                return
            
            if not note:
                messagebox.showerror("错误", "请输入备注用途")
                return
            
            # 生成唯一ID
            token_id = len(self.tokens) + 1
            
            # 保存Token信息
            self.tokens.append({
                'id': token_id,
                'token': token,
                'note': note,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            self._save_tokens()
            self._refresh_token_list()
            token_window.destroy()
        
        ttk.Button(token_window, text="保存", command=save_token).place(x=150, y=200)
        ttk.Button(token_window, text="取消", command=token_window.destroy).place(x=250, y=200)
    
    def _edit_token(self):
        """编辑选中的Token"""
        selection = self.token_listbox.curselection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个Token")
            return
        
        index = selection[0]
        token_data = self.tokens[index]
        
        token_window = tk.Toplevel(self.root)
        token_window.title("编辑 GitHub Token")
        token_window.geometry("450x250")
        token_window.resizable(False, False)
        token_window.transient(self.root)
        token_window.grab_set()

        
        
        ttk.Label(token_window, text="Token:", font=self.default_font).place(x=20, y=20)
        token_entry = ttk.Entry(token_window, width=40, show='*', font=self.default_font)
        token_entry.insert(0, token_data['token'])
        token_entry.place(x=100, y=20)
        
        ttk.Label(token_window, text="备注用途:", font=self.default_font).place(x=20, y=70)
        note_entry = ttk.Entry(token_window, width=40, font=self.default_font)
        note_entry.insert(0, token_data['note'])
        note_entry.place(x=100, y=70)
        
        ttk.Label(token_window, text="Token权限说明:", font=self.default_font).place(x=20, y=100)
        perms_text = tk.Text(token_window, width=45, height=4, font=self.default_font)
        perms_text.place(x=20, y=120)
        perms_text.insert(tk.END, "需要repo权限(读写仓库)\nadmin:repo_hook权限(管理仓库钩子)")
        perms_text.config(state=tk.DISABLED)

        token_entry = ttk.Entry(token_window, width=40, show='*', font=self.default_font)
        token_entry.insert(0, token_data['token'])
        token_entry.place(x=100, y=20)

        # 小眼睛按钮
        show_token_var = tk.IntVar()
        def toggle_token_visibility():
            if show_token_var.get() == 1:
                token_entry.config(show='')
            else:
                token_entry.config(show='*')

        show_token_checkbox = tk.Checkbutton(token_window, text="显示Token", variable=show_token_var, command=toggle_token_visibility)
        show_token_checkbox.place(x=320, y=45)
        
        def update_token():
            token = token_entry.get().strip()
            note = note_entry.get().strip()
            
            if not token:
                messagebox.showerror("错误", "Token不能为空")
                return
            
            if not note:
                messagebox.showerror("错误", "请输入备注用途")
                return
            
            # 更新Token信息
            self.tokens[index] = {
                'id': token_data['id'],
                'token': token,
                'note': note,
                'created_at': token_data['created_at']
            }
            
            self._save_tokens()
            self._refresh_token_list()
            token_window.destroy()
        
        ttk.Button(token_window, text="更新", command=update_token).place(x=150, y=200)
        ttk.Button(token_window, text="取消", command=token_window.destroy).place(x=250, y=200)
    
    def _delete_token(self):
        """删除选中的Token"""
        selection = self.token_listbox.curselection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个Token")
            return
        
        if messagebox.askyesno("确认", "确定要删除这个Token吗？"):
            index = selection[0]
            del self.tokens[index]
            self._save_tokens()
            self._refresh_token_list()
            
            # 如果删除的是当前使用的Token，清空当前Token
            if hasattr(self, 'current_token_id') and self.current_token_id == index + 1:
                self.github_token.set("")
                self.current_token_id = None
                self.current_token_label.config(text="未选择 Token", foreground="red")
    
    def _use_selected_token(self):
        """使用选中的Token"""
        selection = self.token_listbox.curselection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个Token")
            return
        
        index = selection[0]
        token_data = self.tokens[index]
        
        self.github_token.set(token_data['token'])
        self.current_token_id = token_data['id']
        self.current_token_label.config(text=f"{token_data['note']} ({token_data['id']})", foreground="green")
        
        messagebox.showinfo("成功", f"已使用 Token: {token_data['note']}")
        
        # 自动刷新仓库列表
        self._fetch_repos()
    
    def _get_headers(self):
        """获取API请求头"""
        token = self.github_token.get()
        if not token:
            messagebox.showerror("错误", "请先选择一个Token")
            return None
        
        return {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def _fetch_repos(self, search_query=None):
        """获取GitHub仓库列表"""
        self.status_var.set("正在获取仓库列表...")
        self.root.update()
        
        headers = self._get_headers()
        if not headers:
            self.status_var.set("就绪")
            return
        
        # 清空当前列表
        for item in self.repo_tree.get_children():
            self.repo_tree.delete(item)
        
        try:
            page = 1
            self.repos = []
            
            while True:
                if search_query:
                    # 使用搜索API
                    url = f"https://api.github.com/search/repositories?q={search_query}+user:{self._get_username()}&page={page}"
                else:
                    # 获取用户所有仓库
                    url = f"https://api.github.com/user/repos?page={page}&per_page=100"
                
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    if search_query:
                        repo_data = response.json().get('items', [])
                    else:
                        repo_data = response.json()
                    
                    if not repo_data:
                        break
                    
                    self.repos.extend(repo_data)
                    
                    # 添加入表格
                    for repo in repo_data:
                        updated_at = datetime.strptime(repo['updated_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M")
                        visibility = "公开" if repo['private'] == False else "私有"
                        
                        self.repo_tree.insert("", tk.END, values=(
                            repo['name'],
                            repo['description'] if repo['description'] else "",
                            updated_at,
                            visibility
                        ))
                    
                    page += 1
                else:
                    self._handle_api_error(response)
                    break
            
            if search_query:
                self.status_var.set(f"搜索完成，找到 {len(self.repos)} 个仓库")
            else:
                self.status_var.set(f"获取完成，共有 {len(self.repos)} 个仓库")
        
        except Exception as e:
            self.status_var.set(f"获取仓库失败: {str(e)}")
            messagebox.showerror("错误", f"获取仓库列表失败: {str(e)}")
    
    def _get_username(self):
        """获取GitHub用户名"""
        headers = self._get_headers()
        if not headers:
            return None
        
        try:
            response = requests.get("https://api.github.com/user", headers=headers)
            if response.status_code == 200:
                return response.json()['login']
            else:
                self._handle_api_error(response)
                return None
        except Exception as e:
            messagebox.showerror("错误", f"获取用户名失败: {str(e)}")
            return None
    
    def _search_repos(self):
        """搜索仓库"""
        query = self.search_var.get().strip()
        if not query:
            self._fetch_repos()  # 如果搜索框为空，显示全部
        else:
            self._fetch_repos(query)
    
    def _create_repo(self):
        """创建新仓库"""
        if not self.github_token.get():
            messagebox.showerror("错误", "请先选择一个Token")
            return
        
        repo_window = tk.Toplevel(self.root)
        repo_window.title("创建 GitHub 仓库")
        repo_window.geometry("400x300")
        
        ttk.Label(repo_window, text="仓库名称:", font=self.default_font).place(x=20, y=20)
        name_entry = ttk.Entry(repo_window, width=40, font=self.default_font)
        name_entry.place(x=100, y=20)
        
        ttk.Label(repo_window, text="仓库描述:", font=self.default_font).place(x=20, y=60)
        desc_entry = ttk.Entry(repo_window, width=40, font=self.default_font)
        desc_entry.place(x=100, y=60)
        
        # 可见性选择
        ttk.Label(repo_window, text="可见性:", font=self.default_font).place(x=20, y=100)
        visibility_var = tk.StringVar(value="public")
        ttk.Radiobutton(repo_window, text="公开", variable=visibility_var, value="public").place(x=100, y=100)
        ttk.Radiobutton(repo_window, text="私有", variable=visibility_var, value="private").place(x=200, y=100)
        
        def create():
            name = name_entry.get().strip()
            desc = desc_entry.get().strip()
            private = visibility_var.get() == "private"
            
            if not name:
                messagebox.showerror("错误", "仓库名称不能为空")
                return
            
            headers = self._get_headers()
            data = {
                "name": name,
                "description": desc,
                "private": private
            }
            try:
                response = requests.post("https://api.github.com/user/repos", headers=headers, json=data)
                if response.status_code == 201:
                    messagebox.showinfo("成功", "仓库创建成功")
                    self._fetch_repos()
                    repo_window.destroy()
                else:
                    self._handle_api_error(response)
            except Exception as e:
                messagebox.showerror("错误", f"创建仓库失败: {str(e)}")
        
        ttk.Button(repo_window, text="创建", command=create).place(x=150, y=200)
        ttk.Button(repo_window, text="取消", command=repo_window.destroy).place(x=250, y=200)
    
    def _delete_repo(self):
        """删除选中的仓库"""
        if not self.github_token.get():
            messagebox.showerror("错误", "请先选择一个Token")
            return
        
        # 获取选中的仓库
        selected_items = self.repo_tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请先选择一个仓库")
            return
        
        # 确认删除
        repo_name = self.repo_tree.item(selected_items[0])['values'][0]
        if not messagebox.askyesno("确认删除", f"确定要删除仓库 '{repo_name}' 吗？\n此操作不可撤销！"):
            return
        
        # 获取用户名和仓库完整名称
        username = self._get_username()
        if not username:
            return
        
        repo_full_name = f"{username}/{repo_name}"
        
        # 准备API请求
        headers = self._get_headers()
        url = f"https://api.github.com/repos/{repo_full_name}"
        
        try:
            self.status_var.set(f"正在删除仓库: {repo_name}...")
            self.root.update()
            
            response = requests.delete(url, headers=headers)
            
            if response.status_code == 204:
                messagebox.showinfo("成功", f"仓库 '{repo_name}' 已成功删除")
                self._fetch_repos()  # 刷新仓库列表
            else:
                self._handle_api_error(response)
        except Exception as e:
            messagebox.showerror("错误", f"删除仓库失败: {str(e)}")
        finally:
            self.status_var.set("就绪")
    
    def _rename_repo(self):
        """重命名选中的仓库"""
        if not self.github_token.get():
            messagebox.showerror("错误", "请先选择一个Token")
            return
        
        # 获取选中的仓库
        selected_items = self.repo_tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请先选择一个仓库")
            return
        
        current_name = self.repo_tree.item(selected_items[0])['values'][0]
        new_name = simpledialog.askstring("重命名仓库", "请输入新的仓库名称:", initialvalue=current_name)
        
        if not new_name or new_name == current_name:
            return
        
        # 获取用户名
        username = self._get_username()
        if not username:
            return
        
        headers = self._get_headers()
        url = f"https://api.github.com/repos/{username}/{current_name}"
        data = {"name": new_name}
        
        try:
            self.status_var.set(f"正在重命名仓库: {current_name}...")
            self.root.update()
            
            response = requests.patch(url, headers=headers, json=data)
            
            if response.status_code == 200:
                messagebox.showinfo("成功", f"仓库已重命名为: {new_name}")
                self._fetch_repos()  # 刷新仓库列表
            else:
                self._handle_api_error(response)
        except Exception as e:
            messagebox.showerror("错误", f"重命名仓库失败: {str(e)}")
        finally:
            self.status_var.set("就绪")
    
    def _upload_to_repo(self):
        """上传单个文件到选中的仓库"""
        # 获取选中的仓库
        selected_items = self.repo_tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请先选择一个仓库")
            return
        
        repo_name = self.repo_tree.item(selected_items[0])['values'][0]
        
        # 获取用户名
        username = self._get_username()
        if not username:
            return
        
        # 选择要上传的文件
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        
        # 获取相对于选择目录的路径（用于在GitHub上创建相同的目录结构）
        file_name = os.path.basename(file_path)
        
        # 创建上传进度窗口
        progress_window = tk.Toplevel(self.root)
        progress_window.title("上传进度")
        progress_window.geometry("400x150")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        ttk.Label(progress_window, text="正在上传文件...", font=self.default_font).pack(pady=10)
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=100)
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        
        status_label = ttk.Label(progress_window, text="准备中...", font=self.default_font)
        status_label.pack(pady=10)
        
        def upload_file_thread():
            try:
                # 更新进度
                progress_var.set(20)
                status_label.config(text=f"正在上传: {file_name}")
                progress_window.update()
                
                # 读取文件内容
                with open(file_path, 'rb') as file:
                    content = file.read()
                    encoded_content = base64.b64encode(content).decode('utf-8')
                
                # 准备API请求
                headers = self._get_headers()
                url = f"https://api.github.com/repos/{username}/{repo_name}/contents/{file_name}"
                data = {
                    "message": f"Upload {file_name}",
                    "content": encoded_content
                }
                
                # 更新进度
                progress_var.set(60)
                status_label.config(text=f"正在发送请求...")
                progress_window.update()
                
                # 发送API请求
                response = requests.put(url, headers=headers, json=data)
                
                # 更新进度
                progress_var.set(90)
                status_label.config(text=f"处理响应...")
                progress_window.update()
                
                if response.status_code in (200, 201):
                    # 成功
                    progress_var.set(100)
                    status_label.config(text=f"上传成功!")
                    progress_window.update()
                    
                    # 延迟关闭窗口
                    progress_window.after(1000, progress_window.destroy)
                    
                    # 刷新仓库列表
                    self.root.after(1500, self._fetch_repos)
                    
                    # 显示成功消息
                    self.root.after(1500, lambda: messagebox.showinfo("成功", f"文件 '{file_name}' 已成功上传到仓库 '{repo_name}'"))
                else:
                    # 失败
                    self._handle_api_error(response)
                    progress_window.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"上传文件失败: {str(e)}")
                progress_window.destroy()
        
        # 在新线程中执行上传，避免阻塞UI
        threading.Thread(target=upload_file_thread, daemon=True).start()
    
    def _upload_project_to_repo(self):
        """上传整个项目(文件夹)到选中的仓库"""
        # 获取选中的仓库
        selected_items = self.repo_tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请先选择一个仓库")
            return
        
        repo_name = self.repo_tree.item(selected_items[0])['values'][0]
        
        # 获取用户名
        username = self._get_username()
        if not username:
            return
        
        # 选择要上传的文件夹
        folder_path = filedialog.askdirectory()
        if not folder_path:
            return
        
        # 计算文件总数用于进度显示
        total_files = sum([len(files) for r, d, files in os.walk(folder_path)])
        if total_files == 0:
            messagebox.showinfo("提示", "所选文件夹为空")
            return
        
        # 创建上传进度窗口
        progress_window = tk.Toplevel(self.root)
        progress_window.title("上传项目")
        progress_window.geometry("600x200")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        ttk.Label(progress_window, text="正在上传项目...", font=self.default_font).pack(pady=10)
        
        # 主进度条 - 显示总体进度
        main_progress_var = tk.DoubleVar()
        main_progress_bar = ttk.Progressbar(progress_window, variable=main_progress_var, maximum=100)
        main_progress_bar.pack(fill=tk.X, padx=20, pady=5)
        
        # 当前文件进度条
        current_file_progress_var = tk.DoubleVar()
        current_file_progress_bar = ttk.Progressbar(progress_window, variable=current_file_progress_var, maximum=100)
        current_file_progress_bar.pack(fill=tk.X, padx=20, pady=5)
        
        # 状态标签
        status_var = tk.StringVar(value="准备中...")
        ttk.Label(progress_window, textvariable=status_var, font=self.default_font).pack(pady=10)
        
        # 已上传文件计数
        files_uploaded = 0
        files_label = ttk.Label(progress_window, text=f"0/{total_files} 文件已上传", font=self.default_font)
        files_label.pack(pady=5)
        
        def upload_project_thread():
            nonlocal files_uploaded
            headers = self._get_headers()
            
            try:
                # 遍历文件夹中的所有文件和子文件夹
                for root, dirs, files in os.walk(folder_path):
                    # 计算相对于选择目录的路径
                    relative_path = os.path.relpath(root, folder_path)
                    if relative_path == ".":
                        relative_path = ""
                    
                    for filename in files:
                        # 更新当前文件进度
                        current_file_progress_var.set(0)
                        status_var.set(f"正在上传: {filename}")
                        progress_window.update()
                        
                        # 构建完整文件路径
                        file_path = os.path.join(root, filename)
                        
                        # 构建GitHub API路径 (包含相对路径)
                        if relative_path:
                            github_path = f"{relative_path}/{filename}"
                        else:
                            github_path = filename
                        
                        # 读取文件内容
                        try:
                            with open(file_path, 'rb') as file:
                                content = file.read()
                                encoded_content = base64.b64encode(content).decode('utf-8')
                        except Exception as e:
                            status_var.set(f"读取文件失败: {filename}")
                            progress_window.update()
                            continue
                        
                        # 更新当前文件进度
                        current_file_progress_var.set(50)
                        progress_window.update()
                        
                        # 准备API请求
                        url = f"https://api.github.com/repos/{username}/{repo_name}/contents/{github_path}"
                        data = {
                            "message": f"Upload {github_path}",
                            "content": encoded_content
                        }
                        
                        # 检查文件是否已存在 (获取SHA值)
                        try:
                            check_response = requests.get(url, headers=headers)
                            if check_response.status_code == 200:
                                # 文件已存在，需要提供SHA值进行更新
                                sha = check_response.json()['sha']
                                data["sha"] = sha
                        except:
                            pass
                        
                        # 发送API请求
                        try:
                            response = requests.put(url, headers=headers, json=data)
                            
                            if response.status_code not in (200, 201):
                                status_var.set(f"上传失败: {filename} (HTTP {response.status_code})")
                                progress_window.update()
                                continue
                        except Exception as e:
                            status_var.set(f"上传失败: {filename} ({str(e)})")
                            progress_window.update()
                            continue
                        
                        # 更新计数和进度
                        files_uploaded += 1
                        main_progress = (files_uploaded / total_files) * 100
                        main_progress_var.set(main_progress)
                        current_file_progress_var.set(100)
                        files_label.config(text=f"{files_uploaded}/{total_files} 文件已上传")
                        status_var.set(f"已上传: {filename}")
                        progress_window.update()
                
                # 完成上传
                status_var.set("项目上传完成!")
                progress_window.update()
                
                # 延迟关闭窗口
                progress_window.after(1500, progress_window.destroy)
                
                # 刷新仓库列表
                self.root.after(2000, self._fetch_repos)
                
                # 显示成功消息
                self.root.after(2000, lambda: messagebox.showinfo("成功", f"项目已成功上传到仓库 '{repo_name}'\n共上传 {files_uploaded} 个文件"))
            except Exception as e:
                messagebox.showerror("错误", f"上传项目失败: {str(e)}")
                progress_window.destroy()
        
        # 在新线程中执行上传，避免阻塞UI
        threading.Thread(target=upload_project_thread, daemon=True).start()
    
    def _handle_api_error(self, response):
        try:
            error_data = response.json()
            error_message = error_data.get('message', '未知错误')
            messagebox.showerror("API错误", f"请求失败，状态码: {response.status_code}, 错误信息: {error_message}")
        except json.JSONDecodeError:
            messagebox.showerror("API错误", f"请求失败，状态码: {response.status_code}, 无法解析错误信息")

if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubManager(root)
    root.mainloop() 