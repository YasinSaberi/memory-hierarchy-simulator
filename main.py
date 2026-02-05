import tkinter as tk
from tkinter import ttk, messagebox
import random
import time

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

class CacheBlock:
    def __init__(self, tag):
        self.tag = tag
        self.last_access = time.time()       
        self.insertion_time = time.time()    
        self.access_count = 1                

class CacheSet:
    def __init__(self, capacity, policy='LRU'):
        self.capacity = capacity
        self.blocks = []
        self.policy = policy

    def access(self, tag):
        for block in self.blocks:
            if block.tag == tag:
                block.last_access = time.time()
                block.access_count += 1
                return True
        return False

    def insert(self, tag):
        for block in self.blocks:
            if block.tag == tag:
                block.last_access = time.time()
                block.access_count += 1
                return

        if len(self.blocks) >= self.capacity:
            self.replace()
        
        new_block = CacheBlock(tag)
        self.blocks.append(new_block)

    def replace(self):
        if not self.blocks:
            return
        victim = None
        if self.policy == 'LRU':
            victim = min(self.blocks, key=lambda b: b.last_access)
        elif self.policy == 'MRU':
            victim = max(self.blocks, key=lambda b: b.last_access)
        elif self.policy == 'LFU':
            victim = min(self.blocks, key=lambda b: b.access_count)
        elif self.policy == 'FIFO':
            victim = min(self.blocks, key=lambda b: b.insertion_time)
        elif self.policy == 'Random':
            victim = random.choice(self.blocks)   
        if victim:
            self.blocks.remove(victim)

class CacheLevel:
    def __init__(self, name, size_bytes, block_size, associativity, access_time, policy):
        self.name = name
        self.size = size_bytes
        self.block_size = block_size
        self.associativity = associativity
        self.access_time = access_time
        self.policy = policy
        
        if associativity == 0: 
             self.num_sets = 1
             self.associativity = int(size_bytes / block_size)
        else:
             self.num_sets = max(1, int(size_bytes / (block_size * associativity)))
        
        self.sets = {} 
        self.hits = 0
        self.misses = 0

    def get_index_and_tag(self, address):
        index = (address // self.block_size) % self.num_sets
        tag = (address // self.block_size) // self.num_sets
        return index, tag

    def access(self, address):
        index, tag = self.get_index_and_tag(address)
        if index not in self.sets:
            return False   
        if self.sets[index].access(tag):
            self.hits += 1
            return True
        else:
            self.misses += 1
            return False

    def insert(self, address):
        index, tag = self.get_index_and_tag(address)
        if index not in self.sets:
            self.sets[index] = CacheSet(self.associativity, self.policy) 
        self.sets[index].insert(tag)

    def get_stats(self):
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        miss_rate = (self.misses / total * 100) if total > 0 else 0
        return self.hits, self.misses, hit_rate, miss_rate

class MemoryHierarchy:
    def __init__(self, config):
        self.levels = []
        self.levels.append(CacheLevel("L1 Cache", config['l1_size'], config['block_size'], 
                                      config['l1_assoc'], config['l1_time'], config['policy']))
        if config['l2_enabled']:
            self.levels.append(CacheLevel("L2 Cache", config['l2_size'], config['block_size'], 
                                          config['l2_assoc'], config['l2_time'], config['policy']))
        if config['l3_enabled']:
            self.levels.append(CacheLevel("L3 Cache", config['l3_size'], config['block_size'], 
                                          config['l3_assoc'], config['l3_time'], config['policy']))
        
        ram_size_bytes = config['ram_size'] * 1024 * 1024 
        self.levels.append(CacheLevel("Main Memory (RAM)", ram_size_bytes, config['block_size'], 
                                      associativity=8, access_time=config['ram_time'], policy=config['policy']))

        disk_size_bytes = config['disk_size'] * 1024 * 1024 * 1024 
        self.disk_level = CacheLevel("Secondary Memory (Disk)", disk_size_bytes, config['block_size'], 
                                     associativity=1, access_time=config['disk_time'], policy="FIFO")

    def access_memory(self, address):
        total_time = 0
        for i, level in enumerate(self.levels):
            total_time += level.access_time
            is_hit = level.access(address)
            if is_hit:
                for j in range(i):
                     self.levels[j].insert(address)
                return total_time, level.name

        total_time += self.disk_level.access_time
        self.disk_level.hits += 1 
        self.disk_level.insert(address)
        for level in self.levels:
            level.insert(address)
        return total_time, "Disk"

class AccessPatternGenerator:
    def __init__(self, max_address):
        self.max_address = max_address

    def generate_sequential(self, num_requests, stride=4):
        addresses = []
        current_addr = 0
        for _ in range(num_requests):
            addresses.append(current_addr)
            current_addr = (current_addr + stride) % self.max_address
        return addresses

    def generate_random(self, num_requests):
        addresses = []
        for _ in range(num_requests):
            addresses.append(random.randint(0, self.max_address))
        return addresses

    def generate_locality(self, num_requests):
        addresses = []
        current_hotspot = random.randint(0, self.max_address)
        for i in range(num_requests):
            if i % (num_requests // 10) == 0: 
                current_hotspot = random.randint(0, self.max_address)
            offset = int(random.gauss(0, 100))
            addr = abs(current_hotspot + offset) % self.max_address
            addr = addr - (addr % 4)
            addresses.append(addr)
        return addresses

class PerformanceAnalyzer:
    def __init__(self, hierarchy, total_time, num_requests):
        self.hierarchy = hierarchy
        self.total_time = total_time
        self.num_requests = num_requests
        self.amat = total_time / num_requests if num_requests > 0 else 0

    def get_tabular_data(self):
        data = []
        for level in self.hierarchy.levels:
            hits, misses, h_rate, m_rate = level.get_stats()
            data.append((level.name, hits, misses, f"{h_rate:.2f}%", f"{m_rate:.2f}%", f"{level.access_time} ns"))
        
        d_hits, d_misses, _, _ = self.hierarchy.disk_level.get_stats()
        data.append((self.hierarchy.disk_level.name, d_hits, "N/A", "100%", "0%", f"{self.hierarchy.disk_level.access_time} ns"))
        return data

    def get_figure(self):
        if not HAS_MATPLOTLIB:
            return None

        fig = Figure(figsize=(8, 4), dpi=100, facecolor='#2b2b2b')
        
        all_levels = self.hierarchy.levels + [self.hierarchy.disk_level]
        names = [l.name.replace("Cache", "").replace("Memory", "").strip() for l in all_levels] 
        hits = [l.hits for l in all_levels]
        misses = [l.misses for l in all_levels]
        
        ax1 = fig.add_subplot(121)
        ax1.set_facecolor('#2b2b2b')
        x = range(len(names))
        ax1.bar(x, hits, width=0.4, label='Hits', color='#00b894')
        ax1.bar(x, misses, width=0.4, label='Misses', color='#ff7675', bottom=hits)
        ax1.set_xticks(x)
        ax1.set_xticklabels(names, rotation=45, color='white', fontsize=8)
        ax1.set_title('Hits vs Misses', color='white', fontsize=10)
        ax1.tick_params(colors='white')
        for spine in ax1.spines.values(): spine.set_edgecolor('#555555')
        ax1.legend(facecolor='#2b2b2b', labelcolor='white', fontsize=8)

        ax2 = fig.add_subplot(122)
        ax2.set_facecolor('#2b2b2b')
        latencies = [l.access_time for l in all_levels]
        ax2.plot(names, latencies, marker='o', linestyle='-', color='#0984e3', linewidth=2)
        ax2.set_yscale('log')
        ax2.set_title('Latency (ns - Log Scale)', color='white', fontsize=10)
        ax2.set_xticklabels(names, rotation=45, color='white', fontsize=8)
        ax2.tick_params(colors='white')
        for spine in ax2.spines.values(): spine.set_edgecolor('#555555')
        ax2.grid(True, which="both", ls="--", alpha=0.3)

        fig.tight_layout()
        return fig

class SimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Memory Hierarchy Simulator")
        self.root.geometry("1280x850")
        
        self.colors = {
            "bg": "#2d3436",           
            "panel": "#2b2b2b",        
            "text": "#dfe6e9",         
            "accent": "#00b894",       
            "accent_hover": "#55efc4",
            "success": "#00b894",      
            "input_bg": "#636e72"      
        }
        
        self.root.configure(bg=self.colors["bg"])
        self.setup_styles()
        self.create_layout()
        
        self.analyzer = None
        self.chart_canvas = None

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("Panel.TFrame", background=self.colors["panel"], relief="flat")
        
        style.configure("TLabel", background=self.colors["panel"], foreground=self.colors["text"], font=("Segoe UI", 10))
        style.configure("Header.TLabel", background=self.colors["bg"], foreground=self.colors["text"], font=("Segoe UI", 22, "bold"))
        style.configure("SubHeader.TLabel", background=self.colors["panel"], foreground=self.colors["accent"], font=("Segoe UI", 12, "bold"))
        style.configure("Stat.TLabel", background=self.colors["panel"], foreground=self.colors["success"], font=("Consolas", 14, "bold"))

        style.configure("Action.TButton", background=self.colors["accent"], foreground="white", font=("Segoe UI", 11, "bold"), borderwidth=0, padding=10)
        style.map("Action.TButton", background=[("active", self.colors["accent_hover"])])

        style.configure("TCheckbutton", background=self.colors["panel"], foreground=self.colors["text"], font=("Segoe UI", 10))
        style.map("TCheckbutton", background=[("active", self.colors["panel"])])

        style.configure("TEntry", fieldbackground=self.colors["input_bg"], foreground="white", insertcolor="white", borderwidth=0)
        style.configure("TCombobox", fieldbackground=self.colors["input_bg"], foreground="white", arrowcolor="white", borderwidth=0)

        style.configure("Treeview", 
                        background=self.colors["panel"], 
                        foreground="white", 
                        fieldbackground=self.colors["panel"],
                        font=("Segoe UI", 10),
                        rowheight=25,
                        borderwidth=0)
        style.configure("Treeview.Heading", background="#636e72", foreground="white", font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", self.colors["accent"])])

        style.configure("TLabelframe", background=self.colors["panel"], bordercolor="#636e72")
        style.configure("TLabelframe.Label", background=self.colors["panel"], foreground="#b2bec3")

    def create_layout(self):
        header = ttk.Label(self.root, text="MEMORY HIERARCHY SIMULATOR", style="Header.TLabel")
        header.pack(pady=(15, 10))

        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        left_panel = ttk.Frame(main_container, style="Panel.TFrame", padding=15)
        left_panel.pack(side="left", fill="both", expand=False, padx=(0, 10))
        
        self.create_settings_ui(left_panel)

        right_panel = ttk.Frame(main_container, style="Panel.TFrame", padding=15)
        right_panel.pack(side="right", fill="both", expand=True)
        
        self.create_dashboard_ui(right_panel)

    def create_settings_ui(self, parent):
        ttk.Label(parent, text="CONFIGURATION", style="SubHeader.TLabel").pack(anchor="w", pady=(0, 15))

        def add_row(p, row, txt, val, var_name, is_combo=False, vals=None):
            ttk.Label(p, text=txt).grid(row=row, column=0, sticky="w", pady=5)
            if is_combo:
                var = tk.StringVar(value=vals[0])
                ttk.Combobox(p, textvariable=var, values=vals, state="readonly", width=12).grid(row=row, column=1, sticky="e", padx=5)
            else:
                var = tk.IntVar(value=val)
                ttk.Entry(p, textvariable=var, width=10).grid(row=row, column=1, sticky="e", padx=5)
            setattr(self, var_name, var)

        gf = ttk.LabelFrame(parent, text=" Global Settings ")
        gf.pack(fill="x", pady=5)
        add_row(gf, 0, "Policy:", None, "policy_var", True, ["LRU", "LFU", "FIFO", "MRU", "Random"])
        add_row(gf, 1, "Block Size:", 64, "block_size_var")

        cf = ttk.LabelFrame(parent, text=" Caches ")
        cf.pack(fill="x", pady=5)
        
        ttk.Label(cf, text="L1 (32KB)", foreground="#aaa").grid(row=0, column=0, columnspan=2, sticky="w")
        add_row(cf, 1, "Time (ns):", 1, "l1_time_var")
        self.l1_size_var = tk.IntVar(value=32768)
        
        ttk.Separator(cf, orient="horizontal").grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        self.l2_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(cf, text="Enable L2", variable=self.l2_enabled, style="TCheckbutton").grid(row=3, column=0, sticky="w")
        add_row(cf, 4, "Time (ns):", 5, "l2_time_var")
        self.l2_size_var = tk.IntVar(value=262144)

        ttk.Separator(cf, orient="horizontal").grid(row=5, column=0, columnspan=2, sticky="ew", pady=5)
        self.l3_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(cf, text="Enable L3", variable=self.l3_enabled, style="TCheckbutton").grid(row=6, column=0, sticky="w")
        add_row(cf, 7, "Time (ns):", 15, "l3_time_var")
        self.l3_size_var = tk.IntVar(value=2097152)

        sf = ttk.LabelFrame(parent, text=" Memory & Disk ")
        sf.pack(fill="x", pady=5)
        add_row(sf, 0, "RAM (ns):", 100, "ram_time_var")
        add_row(sf, 1, "Disk (ns):", 10000000, "disk_time_var")
        self.ram_size_var = tk.IntVar(value=1024)
        self.disk_size_var = tk.IntVar(value=500)

        wf = ttk.LabelFrame(parent, text=" Workload ")
        wf.pack(fill="x", pady=5)
        add_row(wf, 0, "Requests:", 5000, "num_requests_var")
        add_row(wf, 1, "Pattern:", None, "pattern_var", True, ["Locality (Real)", "Sequential", "Random"])

        ttk.Button(parent, text="START SIMULATION", style="Action.TButton", command=self.run_simulation).pack(fill="x", pady=(20, 0))

    def create_dashboard_ui(self, parent):
        stats_frame = ttk.Frame(parent, style="Panel.TFrame")
        stats_frame.pack(fill="x", pady=(0, 10))
        
        self.status_label = ttk.Label(stats_frame, text="Ready", font=("Segoe UI", 14))
        self.status_label.pack(side="left")
        
        self.amat_label = ttk.Label(stats_frame, text="AMAT: -- ns", style="Stat.TLabel")
        self.amat_label.pack(side="right")

        table_frame = ttk.Frame(parent, style="Panel.TFrame")
        table_frame.pack(fill="x", pady=5)
        
        cols = ("level", "hits", "misses", "hrate", "mrate", "latency")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=6)
        
        headers = ["Level", "Hits", "Misses", "Hit Rate", "Miss Rate", "Latency"]
        widths = [120, 80, 80, 80, 80, 100]
        
        for col, h, w in zip(cols, headers, widths):
            self.tree.heading(col, text=h)
            self.tree.column(col, anchor="center", width=w)
        self.tree.column("level", anchor="w")
        self.tree.pack(fill="x")

        ttk.Label(parent, text="VISUAL ANALYSIS", style="SubHeader.TLabel").pack(anchor="w", pady=(15, 5))
        
        self.chart_frame = ttk.Frame(parent, style="Panel.TFrame")
        self.chart_frame.pack(fill="both", expand=True)
        
        if not HAS_MATPLOTLIB:
            ttk.Label(self.chart_frame, text="Matplotlib not found. Charts unavailable.", foreground="#ff7675").pack(pady=20)

    def run_simulation(self):
        try:
            config = {
                'policy': self.policy_var.get(),
                'block_size': self.block_size_var.get(),
                'l1_size': self.l1_size_var.get(), 'l1_assoc': 4, 'l1_time': self.l1_time_var.get(),
                'l2_enabled': self.l2_enabled.get(), 'l2_size': self.l2_size_var.get(), 'l2_assoc': 8, 'l2_time': self.l2_time_var.get(),
                'l3_enabled': self.l3_enabled.get(), 'l3_size': self.l3_size_var.get(), 'l3_assoc': 16, 'l3_time': self.l3_time_var.get(),
                'ram_size': self.ram_size_var.get(), 'ram_time': self.ram_time_var.get(),
                'disk_size': self.disk_size_var.get(), 'disk_time': self.disk_time_var.get()
            }
        except ValueError:
            messagebox.showerror("Error", "Invalid numeric input.")
            return

        self.status_label.config(text="Simulating...", foreground="#fdcb6e")
        self.root.update()

        hierarchy = MemoryHierarchy(config)
        generator = AccessPatternGenerator(config['ram_size'] * 1024 * 1024)
        
        num = self.num_requests_var.get()
        pat = self.pattern_var.get()
        if pat == "Sequential": addrs = generator.generate_sequential(num)
        elif pat == "Random": addrs = generator.generate_random(num)
        else: addrs = generator.generate_locality(num)
        
        start = time.time()
        t_mem = 0
        for a in addrs:
            t, _ = hierarchy.access_memory(a)
            t_mem += t
        dur = time.time() - start

        self.analyzer = PerformanceAnalyzer(hierarchy, t_mem, num)

        for i in self.tree.get_children(): self.tree.delete(i)
        data = self.analyzer.get_tabular_data()
        for row in data:
            self.tree.insert("", "end", values=row)

        self.status_label.config(text=f"Simulation Complete ({dur:.3f}s)", foreground=self.colors["success"])
        self.amat_label.config(text=f"AMAT: {self.analyzer.amat:.2f} ns")

        if HAS_MATPLOTLIB:
            fig = self.analyzer.get_figure()
            if fig:
                if self.chart_canvas:
                    self.chart_canvas.get_tk_widget().destroy()
                
                self.chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
                self.chart_canvas.draw()
                self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = SimulatorApp(root)
    root.mainloop()