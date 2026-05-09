import tkinter as tk
from tkinter import ttk
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# (display_name, used_col, period_col, show_col, wear_col)
PARTS = [
    ("Chain",         "chain_used_miles",         "chain_miles",          None,                   "wear_chain"),
    ("Cassette",      "cassette_used_miles",       "cassette_miles",       None,                   "wear_cassette"),
    ("Front Fork",    "front_fork_used_miles",     "front_fork_miles",     "front_fork_show",      "wear_front_fork"),
    ("Rear Shock",    "rear_shock_used_miles",     "rear_shock_miles",     "rear_suspension_show", "wear_rear_shock"),
    ("Chainring",     "chain_ring_used_miles",     "chain_ring_miles",     None,                   "wear_chainring"),
    ("Bot. Bracket",  "bottom_bracket_used_miles", "bottom_bracket_miles", None,                   "wear_bot_bracket"),
    ("Sealant (hrs)", "sealant_used_hours",        "sealant_refresh_hours","sealant_show",         "wear_sealant"),
    ("Brake Pads",    "brake_pads_used_miles",     "brake_pads_miles",     "brake_pads_show",      "wear_brake_pads"),
    ("Brake Bleed",   "brake_bleed_used_miles",    "brake_bleed_miles",    "brake_bleed_show",     "wear_brake_bleed"),
    ("Brake Rotors",  "brake_rotors_used_miles",   "brake_rotors_miles",   "brake_rotors_show",    "wear_brake_rotors"),
    ("Tires",         "tires_used_miles",          "tires_miles",          None,                   "wear_tires"),
    ("Dropper",       "dropper_used_miles",        "dropper_miles",        "dropper_show",         "wear_dropper"),
]
WEAR_COLS = [p[4] for p in PARTS]


def load_data():
    part_data = pd.read_csv(os.path.join(BASE_DIR, 'part_data.csv'), encoding='latin-1')
    users     = pd.read_csv(os.path.join(BASE_DIR, 'users.csv'))
    shops     = pd.read_csv(os.path.join(BASE_DIR, 'shops.csv'))
    periods   = pd.read_csv(os.path.join(BASE_DIR, 'part_service_periods.csv'))
    history   = pd.read_csv(os.path.join(BASE_DIR, 'part_history.csv'))

    period_cols = [
        'strava_bike_id', 'chain_miles', 'cassette_miles', 'front_fork_miles',
        'rear_shock_miles', 'chain_ring_miles', 'bottom_bracket_miles',
        'sealant_refresh_hours', 'brake_bleed_miles', 'brake_pads_miles',
        'brake_rotors_miles', 'tires_miles', 'dropper_miles',
    ]
    df = part_data.merge(periods[period_cols], on='strava_bike_id', how='left')
    df = df.merge(
        users[['strava_user_id', 'first_name', 'last_name', 'shop_token']],
        on='strava_user_id', how='left',
    )
    df = df.merge(shops[['shop_token', 'shop_name']], on='shop_token', how='left')

    for _, used_col, period_col, _, wear_col in PARTS:
        def _wear(r, u=used_col, p=period_col):
            u_val = r.get(u)
            p_val = r.get(p)
            if pd.isna(u_val) or pd.isna(p_val) or float(p_val) <= 0:
                return float('nan')
            return max(0.0, float(u_val)) / float(p_val) * 100.0
        df[wear_col] = df.apply(_wear, axis=1)

    df['bike_label'] = (
        df['strava_bike_name'].fillna('Unknown')
        + ' ('
        + df['first_name'].fillna('').str.strip()
        + ' '
        + df['last_name'].fillna('').str.strip()
        + ')'
    )

    history['date_replaced'] = pd.to_datetime(history['date_replaced'], errors='coerce')
    history = history.merge(
        users[['strava_user_id', 'first_name', 'last_name']], on='strava_user_id', how='left'
    )
    history = history.merge(
        part_data[['strava_bike_id', 'strava_bike_name']], on='strava_bike_id', how='left'
    )

    return df, history


def _embed(fig, parent, fill='both', expand=True):
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=fill, expand=expand)
    return canvas


class KORApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('KOR Bike Maintenance Analysis')
        self.root.geometry('1280x820')
        self.root.minsize(900, 600)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook.Tab', font=('Helvetica', 11, 'bold'), padding=[14, 6])
        style.configure('Heading.TLabel', font=('Helvetica', 11, 'bold'))

        try:
            plt.style.use('seaborn-v0_8-darkgrid')
        except OSError:
            try:
                plt.style.use('seaborn-darkgrid')
            except OSError:
                pass

        self.df, self.history = load_data()

        nb = ttk.Notebook(self.root)
        nb.pack(fill='both', expand=True, padx=8, pady=8)

        for title, builder in [
            ('  Shop Dashboard  ',      self.build_dashboard),
            ('  Part Health Monitor  ', self.build_part_health),
            ('  Service History  ',     self.build_service_history),
            ('  Fleet Analytics  ',     self.build_fleet_analytics),
        ]:
            tab = ttk.Frame(nb)
            nb.add(tab, text=title)
            builder(tab)

    # ── Tab 1: Shop Dashboard ──────────────────────────────────────────────
    def build_dashboard(self, frame):
        wear_data = self.df[WEAR_COLS]
        overdue   = int((wear_data >= 100).sum().sum())
        due_soon  = int(((wear_data >= 70) & (wear_data < 100)).sum().sum())

        kpi_frame = tk.Frame(frame, bg='#e8e8e8')
        kpi_frame.pack(fill='x', padx=12, pady=(12, 4))

        kpis = [
            ('Total Bikes',   len(self.df),                          '#1565C0'),
            ('Active Users',  self.df['strava_user_id'].nunique(),   '#2E7D32'),
            ('Parts Overdue', overdue,                                '#B71C1C'),
            ('Due Soon',      due_soon,                               '#E65100'),
        ]
        for label, value, color in kpis:
            card = tk.Frame(kpi_frame, bg=color, padx=20, pady=12, relief='raised', bd=2)
            card.pack(side='left', expand=True, fill='x', padx=8, pady=6)
            tk.Label(card, text=str(value), font=('Helvetica', 26, 'bold'),
                     bg=color, fg='white').pack()
            tk.Label(card, text=label, font=('Helvetica', 10),
                     bg=color, fg='#dddddd').pack()

        chart_frame = tk.Frame(frame)
        chart_frame.pack(fill='both', expand=True, padx=12, pady=8)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        fig.suptitle('Shop & Fleet Overview', fontsize=13, fontweight='bold')

        shop_counts = (
            self.df['shop_name'].fillna('Unknown Shop')
            .value_counts()
            .sort_values(ascending=True)
        )
        bars = ax1.barh(shop_counts.index, shop_counts.values, color='#1E88E5', edgecolor='white')
        ax1.set_title('Bikes per Shop')
        ax1.set_xlabel('Number of Bikes')
        for bar in bars:
            w = bar.get_width()
            ax1.text(w + 0.1, bar.get_y() + bar.get_height() / 2,
                     str(int(w)), va='center', fontsize=9)

        type_counts = (
            self.df['bike_type']
            .replace('', 'Unknown').fillna('Unknown')
            .value_counts()
        )
        colors_pie = plt.cm.tab20.colors[:len(type_counts)]
        wedges, _, autotexts = ax2.pie(
            type_counts.values,
            labels=None,
            autopct=lambda pct: f'{pct:.0f}%' if pct >= 4 else '',
            colors=colors_pie, startangle=90,
            wedgeprops=dict(edgecolor='white', linewidth=1),
        )
        for t in autotexts:
            t.set_fontsize(8)
        ax2.legend(wedges, type_counts.index, loc='center left',
                   bbox_to_anchor=(1, 0.5), fontsize=8, framealpha=0.8)
        ax2.set_title('Bike Type Distribution')

        fig.tight_layout()
        _embed(fig, chart_frame)

    # ── Tab 2: Part Health Monitor ─────────────────────────────────────────
    def build_part_health(self, frame):
        ctrl = tk.Frame(frame)
        ctrl.pack(fill='x', padx=12, pady=10)

        tk.Label(ctrl, text='Select Bike:', font=('Helvetica', 11, 'bold')).pack(side='left')
        self.bike_var = tk.StringVar()
        labels = sorted(self.df['bike_label'].dropna().unique().tolist())
        cb = ttk.Combobox(ctrl, textvariable=self.bike_var, values=labels,
                          width=68, state='readonly', font=('Helvetica', 10))
        cb.pack(side='left', padx=10)
        cb.bind('<<ComboboxSelected>>', self._on_bike_selected)

        self.health_fig, self.health_ax = plt.subplots(figsize=(11, 6))
        self.health_canvas = FigureCanvasTkAgg(self.health_fig, master=frame)
        self.health_canvas.get_tk_widget().pack(fill='both', expand=True, padx=12, pady=6)

        if labels:
            cb.set(labels[0])
            self._on_bike_selected(None)

    def _on_bike_selected(self, _event):
        label = self.bike_var.get()
        rows = self.df[self.df['bike_label'] == label]
        if rows.empty:
            return
        row = rows.iloc[0]

        names, values, bar_colors = [], [], []
        for display, _, _, show_col, wear_col in PARTS:
            if show_col is not None:
                show_val = row.get(show_col, 0)
                if pd.isna(show_val) or not bool(show_val):
                    continue
            val = row.get(wear_col, float('nan'))
            if pd.isna(val):
                continue
            val = float(val)
            names.append(display)
            values.append(min(val, 160.0))
            bar_colors.append(
                '#EF5350' if val >= 100 else
                '#FFA726' if val >= 70  else
                '#66BB6A'
            )

        ax = self.health_ax
        ax.clear()

        if names:
            bars = ax.barh(names, values, color=bar_colors, edgecolor='white', linewidth=0.6)
            ax.axvline(100, color='#EF5350', linestyle='--', linewidth=1.5,
                       alpha=0.8, label='Service Due (100%)')
            ax.axvline(70,  color='#FFA726', linestyle='--', linewidth=1.5,
                       alpha=0.6, label='Due Soon (70%)')
            for bar, val in zip(bars, values):
                ax.text(
                    bar.get_width() + 0.5,
                    bar.get_y() + bar.get_height() / 2,
                    f'{val:.0f}%', va='center', fontsize=9,
                )
            ax.set_xlim(0, max(max(values) + 22, 120))
            ax.set_xlabel('Wear (% of service interval)')
            ax.set_title(f'Part Health: {label}', fontsize=12, fontweight='bold')
            ax.legend(loc='lower right')
        else:
            ax.text(0.5, 0.5, 'No part data available for this bike',
                    ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title(f'Part Health: {label}', fontsize=12, fontweight='bold')

        self.health_fig.tight_layout()
        self.health_canvas.draw()

    # ── Tab 3: Service History ─────────────────────────────────────────────
    def build_service_history(self, frame):
        chart_frame = tk.Frame(frame)
        chart_frame.pack(fill='x', padx=12, pady=(8, 4))

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        fig.suptitle('Service History Analysis', fontsize=13, fontweight='bold')

        part_counts = self.history['part_type'].value_counts().sort_values()
        bars = ax1.barh(part_counts.index, part_counts.values,
                        color='#5C6BC0', edgecolor='white')
        ax1.set_title('All-Time Replacements by Part Type')
        ax1.set_xlabel('Replacements')
        for bar in bars:
            w = bar.get_width()
            ax1.text(w + 0.1, bar.get_y() + bar.get_height() / 2,
                     str(int(w)), va='center', fontsize=8)

        dated = self.history.dropna(subset=['date_replaced'])
        if not dated.empty:
            monthly = dated.groupby(dated['date_replaced'].dt.to_period('M')).size()
            monthly.index = monthly.index.astype(str)
            ax2.bar(monthly.index, monthly.values, color='#26A69A', edgecolor='white')
            ax2.set_title('Service Events per Month')
            ax2.set_xlabel('Month')
            ax2.set_ylabel('Events')
            stride = max(1, len(monthly) // 10)
            ax2.set_xticks(range(0, len(monthly), stride))
            ax2.set_xticklabels(
                [monthly.index[i] for i in range(0, len(monthly), stride)],
                rotation=45, ha='right', fontsize=8,
            )
        else:
            ax2.text(0.5, 0.5, 'No dated records', ha='center', va='center',
                     transform=ax2.transAxes)
            ax2.set_title('Service Events per Month')

        fig.tight_layout()
        fig.subplots_adjust(left=0.18)
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

        tk.Label(frame, text='Recent Service Events (last 30)',
                 font=('Helvetica', 11, 'bold')).pack(padx=12, pady=(6, 2), anchor='w')

        tree_frame = tk.Frame(frame)
        tree_frame.pack(fill='both', expand=True, padx=12, pady=(0, 10))

        cols = ('Date', 'Bike', 'Part', 'Miles Used', 'Reason')
        tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=10)
        col_widths = {'Date': 100, 'Bike': 200, 'Part': 120, 'Miles Used': 90, 'Reason': 110}
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=col_widths[col], anchor='center')

        recent = (
            self.history.dropna(subset=['date_replaced'])
            .sort_values('date_replaced', ascending=False)
            .head(30)
        )
        for _, r in recent.iterrows():
            date_str = r['date_replaced'].strftime('%Y-%m-%d')
            bike_str = str(r.get('strava_bike_name') or '')[:35]
            tree.insert('', 'end', values=(
                date_str,
                bike_str,
                str(r.get('part_type') or ''),
                f"{float(r.get('used_miles') or 0):.0f}",
                str(r.get('broken_worn') or ''),
            ))

        sb = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        tree.pack(side='left', fill='both', expand=True)

    # ── Tab 4: Fleet Analytics ─────────────────────────────────────────────
    def build_fleet_analytics(self, frame):
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle('Fleet Analytics', fontsize=13, fontweight='bold')

        self.df['full_name'] = (
            self.df['first_name'].fillna('').str.strip()
            + ' '
            + self.df['last_name'].fillna('').str.strip()
        ).str.strip().replace('', 'Unknown')
        user_miles = (
            self.df.groupby('full_name')['total_miles'].sum()
            .sort_values(ascending=False)
            .head(15)
        )
        ax1.barh(user_miles.index[::-1], user_miles.values[::-1],
                 color='#AB47BC', edgecolor='white')
        ax1.set_title('Top 15 Users by Total Miles')
        ax1.set_xlabel('Total Miles')

        valid = self.df[
            self.df['bike_type'].notna() & (self.df['bike_type'].str.strip() != '')
        ]
        type_miles = (
            valid.groupby('bike_type')['total_miles'].mean()
            .sort_values(ascending=False)
        )
        ax2.bar(type_miles.index, type_miles.values, color='#26C6DA', edgecolor='white')
        ax2.set_title('Avg Miles by Bike Type')
        ax2.set_ylabel('Average Miles')
        ax2.tick_params(axis='x', rotation=45, labelsize=8)

        bw = self.history[self.history['broken_worn'].isin(['broke', 'worn_out'])]
        if not bw.empty:
            bw_counts = bw.groupby(['part_type', 'broken_worn']).size().unstack(fill_value=0)
            bw_sorted = (
                bw_counts
                .assign(_total=bw_counts.sum(axis=1))
                .sort_values('_total', ascending=False)
                .drop('_total', axis=1)
                .head(10)
            )
            bw_sorted.plot(kind='bar', ax=ax3, color=['#EF5350', '#42A5F5'],
                           edgecolor='white')
            ax3.set_title('Broken vs Worn Out (Top 10 Parts)')
            ax3.set_xlabel('')
            ax3.set_ylabel('Count')
            ax3.tick_params(axis='x', rotation=45, labelsize=8)
            ax3.legend(title='Reason', fontsize=8)
        else:
            ax3.text(0.5, 0.5, 'No broken/worn data', ha='center', va='center',
                     transform=ax3.transAxes)
            ax3.set_title('Broken vs Worn Out')

        fig.tight_layout()
        _embed(fig, frame)


if __name__ == '__main__':
    app = KORApp()
    app.root.mainloop()
