import threading
import datetime
import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
import bcrypt

from pg_db import connect_pg, get_cursor, log_access
from yolo_runner import run_yolo

#  Theme constants
DARK_BG     = "#0f1117"
CARD_BG     = "#1a1d27"
SIDEBAR_BG  = "#13151f"
ACCENT      = "#4f8ef7"
ACCENT2     = "#7c3aed"
SUCCESS     = "#22c55e"
DANGER      = "#ef4444"
WARNING     = "#f59e0b"
TEXT_PRI    = "#f1f5f9"
TEXT_SEC    = "#94a3b8"
BORDER      = "#2d3148"

FONT_H1     = ("Segoe UI", 22, "bold")
FONT_H2     = ("Segoe UI", 16, "bold")
FONT_H3     = ("Segoe UI", 13, "bold")
FONT_BODY   = ("Segoe UI", 11)
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 10)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

#  Helpers

def styled_button(parent, text, command, color=ACCENT, width=160, **kw):
    return ctk.CTkButton(
        parent, text=text, command=command,
        fg_color=color, hover_color=_darken(color),
        font=FONT_BODY, corner_radius=8,
        width=width, height=36, **kw
    )

def _darken(hex_color: str, factor=0.8) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return "#{:02x}{:02x}{:02x}".format(int(r*factor), int(g*factor), int(b*factor))

def card(parent, **kw) -> ctk.CTkFrame:
    return ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12,
                        border_width=1, border_color=BORDER, **kw)

def section_label(parent, text: str):
    ctk.CTkLabel(parent, text=text, font=FONT_H2,
                 text_color=TEXT_PRI).pack(anchor="w", pady=(0, 12))

def subtle_label(parent, text: str, **kw):
    return ctk.CTkLabel(parent, text=text, font=FONT_SMALL,
                        text_color=TEXT_SEC, **kw)

def field_label(parent, text: str):
    ctk.CTkLabel(parent, text=text, font=FONT_BODY,
                 text_color=TEXT_SEC).pack(anchor="w")

def entry(parent, placeholder="", width=280, show="") -> ctk.CTkEntry:
    return ctk.CTkEntry(parent, placeholder_text=placeholder,
                        width=width, height=38, corner_radius=8,
                        fg_color="#1e2130", border_color=BORDER,
                        text_color=TEXT_PRI, font=FONT_BODY, show=show)

def combo(parent, values, width=280) -> ctk.CTkOptionMenu:
    return ctk.CTkOptionMenu(parent, values=values, width=width, height=38,
                             fg_color="#1e2130", button_color=ACCENT,
                             dropdown_fg_color=CARD_BG,
                             text_color=TEXT_PRI, font=FONT_BODY)

def build_treeview(parent, columns: list[tuple], height=15):
    """columns = [(col_id, heading, width), ...]"""
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Custom.Treeview",
                    background=CARD_BG, foreground=TEXT_PRI,
                    fieldbackground=CARD_BG, rowheight=30,
                    font=FONT_BODY)
    style.configure("Custom.Treeview.Heading",
                    background=SIDEBAR_BG, foreground=ACCENT,
                    font=FONT_H3, relief="flat")
    style.map("Custom.Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", "#fff")])

    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True, pady=6)

    col_ids = [c[0] for c in columns]
    tree = ttk.Treeview(frame, columns=col_ids, show="headings",
                        style="Custom.Treeview", height=height)

    for col_id, heading, width in columns:
        tree.heading(col_id, text=heading)
        tree.column(col_id, width=width, anchor="center")

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    return tree

def toplevel_window(title: str, width=600, height=520) -> ctk.CTkToplevel:
    win = ctk.CTkToplevel()
    win.title(title)
    win.geometry(f"{width}x{height}")
    win.configure(fg_color=DARK_BG)
    win.grab_set()
    return win

def show_error(msg: str):
    messagebox.showerror("Error", msg)

def show_info(msg: str):
    messagebox.showinfo("Success", msg)

#  Login

class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Student Record System — Login")
        self.geometry("440x560")
        self.resizable(False, False)
        self.configure(fg_color=DARK_BG)
        self._logged_in_user = None
        self._build_ui()

    def _build_ui(self):
        # Top accent bar
        bar = ctk.CTkFrame(self, fg_color=ACCENT, height=4, corner_radius=0)
        bar.pack(fill="x")

        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(expand=True, fill="both", padx=50)

        # Logo / title
        ctk.CTkLabel(outer, text="🎓", font=("Segoe UI", 48)).pack(pady=(40, 4))
        ctk.CTkLabel(outer, text="Student Record System",
                     font=FONT_H1, text_color=TEXT_PRI).pack()
        subtle_label(outer, "Face-ID Attendance Platform").pack(pady=(4, 30))

        # Form card
        f = card(outer)
        f.pack(fill="x", pady=4)
        fp = ctk.CTkFrame(f, fg_color="transparent")
        fp.pack(padx=24, pady=24, fill="x")

        field_label(fp, "Email address")
        self._email = entry(fp, "teacher@giki.edu.pk", width=320)
        self._email.pack(fill="x", pady=(2, 12))

        field_label(fp, "Password")
        self._pw = entry(fp, "••••••••", width=320, show="*")
        self._pw.pack(fill="x", pady=(2, 4))

        # Role badge
        self._role_var = ctk.StringVar(value="teacher")
        role_row = ctk.CTkFrame(fp, fg_color="transparent")
        role_row.pack(fill="x", pady=(10, 4))
        ctk.CTkLabel(role_row, text="Role:", font=FONT_BODY,
                     text_color=TEXT_SEC).pack(side="left")
        for val, label in [("teacher", "Teacher"), ("student", "Student")]:
            ctk.CTkRadioButton(
                role_row, text=label, variable=self._role_var, value=val,
                font=FONT_BODY, text_color=TEXT_PRI,
                fg_color=ACCENT
            ).pack(side="left", padx=10)

        styled_button(fp, "Sign In", self._login, width=320).pack(fill="x", pady=(18, 0))

        subtle_label(outer,
            "Students may only view their own records.\n"
            "Teachers have full management access."
        ).pack(pady=16)

    def _login(self):
        email    = self._email.get().strip()
        password = self._pw.get()
        role     = self._role_var.get()

        if not email or not password:
            show_error("Please enter both email and password.")
            return

        try:
            conn = connect_pg()
            cur  = get_cursor(conn)
            cur.execute(
                "SELECT user_id, password_hash, role FROM users WHERE email = %s",
                (email,)
            )
            row = cur.fetchone()
            conn.close()
        except Exception as e:
            show_error(f"Database error:\n{e}")
            return

        if row is None:
            show_error("No account found with that email.")
            return

        # Accept bcrypt hashes OR plain-text fallback for dev seeds
        pw_hash = row["password_hash"]
        try:
            valid = bcrypt.checkpw(password.encode(), pw_hash.encode())
        except Exception:
            valid = (password == pw_hash)   # plain-text dev seed fallback

        if not valid:
            show_error("Incorrect password.")
            return

        if row["role"] != role:
            show_error(f"This account is registered as '{row['role']}', not '{role}'.")
            return

        user_id = row["user_id"]

        # Log the login event
        try:
            _lconn = connect_pg()
            log_access(_lconn, user_id, f"login_{role}")
            _lconn.commit()
            _lconn.close()
        except Exception:
            pass

        self.destroy()

        if role == "teacher":
            TeacherDashboard(user_id=user_id, email=email)
        else:
            StudentPortal(user_id=user_id, email=email)


#  Teacher Dashboard

class TeacherDashboard(ctk.CTk):
    NAV_ITEMS = [
        ("🏠", "Dashboard",         "dashboard"),
        ("👥", "Students",          "students"),
        ("📚", "Courses",           "courses"),
        ("📋", "Attendance",        "attendance"),
        ("✏️",  "Manual Attendance", "manual_att"),
        ("📊", "Marks",             "marks"),
        ("➕", "Add Student",       "add_student"),
    ]

    def __init__(self, user_id: int, email: str):
        super().__init__()
        self.user_id = user_id
        self.email   = email
        self.title("Student Record System — Teacher Dashboard")
        self.geometry("1280x780")
        self.configure(fg_color=DARK_BG)
        self._active_page = None
        self._build_layout()
        self._show_page("dashboard")
        self.mainloop()

    # ── layout skeleton 
    def _build_layout(self):
        # Sidebar
        self._sidebar = ctk.CTkFrame(self, fg_color=SIDEBAR_BG,
                                     width=220, corner_radius=0)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        # Sidebar header
        ctk.CTkLabel(self._sidebar, text="🎓",
                     font=("Segoe UI", 32)).pack(pady=(28, 2))
        ctk.CTkLabel(self._sidebar, text="SRS",
                     font=FONT_H1, text_color=TEXT_PRI).pack()
        subtle_label(self._sidebar, "Teacher Portal").pack(pady=(2, 20))

        ctk.CTkFrame(self._sidebar, fg_color=BORDER,
                     height=1).pack(fill="x", padx=16, pady=4)

        # Nav buttons
        self._nav_btns: dict[str, ctk.CTkButton] = {}
        for icon, label, key in self.NAV_ITEMS:
            btn = ctk.CTkButton(
                self._sidebar, text=f"  {icon}  {label}",
                anchor="w", width=200, height=40, corner_radius=8,
                fg_color="transparent", hover_color="#1e2130",
                font=FONT_BODY, text_color=TEXT_SEC,
                command=lambda k=key: self._show_page(k)
            )
            btn.pack(pady=2, padx=10)
            self._nav_btns[key] = btn

        # Bottom logout
        ctk.CTkFrame(self._sidebar, fg_color=BORDER,
                     height=1).pack(fill="x", padx=16, pady=8, side="bottom")
        ctk.CTkButton(
            self._sidebar, text="  ⏻  Logout", anchor="w",
            width=200, height=38, corner_radius=8,
            fg_color="transparent", hover_color="#2c1515",
            font=FONT_BODY, text_color=DANGER,
            command=self._logout
        ).pack(side="bottom", padx=10, pady=4)
        subtle_label(self._sidebar, self.email).pack(side="bottom", pady=4)

        # Main content area
        self._content = ctk.CTkFrame(self, fg_color=DARK_BG, corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

    def _clear_content(self):
        for w in self._content.winfo_children():
            w.destroy()

    def _set_nav_active(self, key: str):
        for k, btn in self._nav_btns.items():
            if k == key:
                btn.configure(fg_color="#1e2130", text_color=ACCENT)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_SEC)

    def _show_page(self, key: str):
        self._active_page = key
        self._set_nav_active(key)
        self._clear_content()
        pages = {
            "dashboard":  self._page_dashboard,
            "students":   self._page_students,
            "courses":    self._page_courses,
            "attendance": self._page_attendance,
            "manual_att": self._page_manual_att,
            "marks":      self._page_marks,
            "add_student":self._page_add_student,
        }
        pages.get(key, self._page_dashboard)()

    def _logout(self):
        self.destroy()
        LoginApp().mainloop()

    # ── header helper 
    def _page_header(self, title: str, subtitle: str = ""):
        hdr = ctk.CTkFrame(self._content, fg_color="transparent")
        hdr.pack(fill="x", padx=32, pady=(28, 4))
        ctk.CTkLabel(hdr, text=title, font=FONT_H1,
                     text_color=TEXT_PRI).pack(anchor="w")
        if subtitle:
            subtle_label(hdr, subtitle).pack(anchor="w", pady=(2, 0))
        ctk.CTkFrame(self._content, fg_color=BORDER,
                     height=1).pack(fill="x", padx=32, pady=8)

    
    #  PAGE: Dashboard overview
    def _page_dashboard(self):
        # Scrollable so nothing gets cut off on smaller screens
        scroll = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Greeting banner 
        import datetime as _dt
        hour = _dt.datetime.now().hour
        greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")

        banner = ctk.CTkFrame(scroll, fg_color="#161928", corner_radius=0)
        banner.pack(fill="x")
        bp = ctk.CTkFrame(banner, fg_color="transparent")
        bp.pack(padx=36, pady=20, anchor="w")
        ctk.CTkLabel(bp, text=f"{greeting}, Ali 👋",
                     font=("Segoe UI", 20, "bold"), text_color=TEXT_PRI).pack(anchor="w")
        ctk.CTkLabel(bp, text=f"Here's what's happening  •  {_dt.date.today().strftime('%A, %d %B %Y')}",
                     font=FONT_BODY, text_color=TEXT_SEC).pack(anchor="w", pady=(2, 0))

        # ── Pull all data 
        try:
            conn = connect_pg()
            cur  = get_cursor(conn)

            cur.execute("SELECT COUNT(*) AS n FROM students WHERE is_active")
            n_students = cur.fetchone()["n"]

            cur.execute("SELECT COUNT(*) AS n FROM courses WHERE is_active")
            n_courses = cur.fetchone()["n"]

            cur.execute("SELECT COUNT(*) AS n FROM enrollments")
            n_enroll = cur.fetchone()["n"]

            cur.execute("""
                SELECT COUNT(*) AS n FROM attendance
                WHERE attendance_date = CURRENT_DATE AND status = 'present'
            """)
            today_present = cur.fetchone()["n"]

            cur.execute("""
                SELECT COUNT(*) AS n FROM attendance
                WHERE attendance_date = CURRENT_DATE AND status = 'absent'
            """)
            today_absent = cur.fetchone()["n"]

            cur.execute("""
                SELECT COUNT(*) AS n FROM face_recognition_log
                WHERE DATE(recognized_at) = CURRENT_DATE AND success = TRUE
            """)
            today_scans = cur.fetchone()["n"]

            # Per-student attendance rate
            cur.execute("""
                SELECT s.first_name || ' ' || s.last_name AS name,
                       s.roll_number,
                       COUNT(*) FILTER (WHERE a.status = 'present') AS present,
                       COUNT(*) AS total
                FROM students s
                LEFT JOIN attendance a USING (student_id)
                WHERE s.is_active
                GROUP BY s.student_id, s.first_name, s.last_name, s.roll_number
                ORDER BY s.roll_number
            """)
            student_rates = cur.fetchall()

            # Recent activity — last 8 attendance events
            cur.execute("""
                SELECT s.first_name || ' ' || s.last_name AS student,
                       c.course_code, a.status, a.marked_via,
                       a.attendance_date, a.check_in_time
                FROM attendance a
                JOIN students s USING (student_id)
                JOIN courses  c USING (course_id)
                ORDER BY a.attendance_date DESC,
                         COALESCE(a.check_in_time, '00:00'::time) DESC
                LIMIT 8
            """)
            recent = cur.fetchall()

            # Course attendance summary
            cur.execute("""
                SELECT c.course_code, c.course_name,
                       COUNT(*) FILTER (WHERE a.status = 'present') AS present,
                       COUNT(*) AS total
                FROM courses c
                LEFT JOIN attendance a USING (course_id)
                WHERE c.is_active
                GROUP BY c.course_id, c.course_code, c.course_name
                ORDER BY c.course_code
            """)
            course_rates = cur.fetchall()

            conn.close()
        except Exception as e:
            show_error(f"DB error: {e}")
            return

        # ── Stat cards row 
        cards_row = ctk.CTkFrame(scroll, fg_color="transparent")
        cards_row.pack(fill="x", padx=28, pady=(20, 4))

        # muted icon bg: pre-computed since CTk doesn't support 8-digit hex
        _icon_bg_map = {
            ACCENT:  "#152033",
            ACCENT2: "#1e1333",
            SUCCESS: "#122212",
            WARNING: "#2a1f08",
        }

        def stat_card(parent, icon, value, label, sublabel, accent_color):
            c = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=14,
                             border_width=1, border_color=BORDER)
            c.pack(side="left", expand=True, fill="both", padx=8)

            top = ctk.CTkFrame(c, fg_color="transparent")
            top.pack(padx=20, pady=(18, 4), fill="x")

            # Icon circle
            icon_bg = ctk.CTkFrame(top, fg_color=_icon_bg_map.get(accent_color, "#1e2130"),
                                   width=44, height=44, corner_radius=12)
            icon_bg.pack(side="left")
            icon_bg.pack_propagate(False)
            ctk.CTkLabel(icon_bg, text=icon,
                         font=("Segoe UI", 20)).pack(expand=True)

            txt = ctk.CTkFrame(top, fg_color="transparent")
            txt.pack(side="left", padx=(14, 0))
            ctk.CTkLabel(txt, text=str(value),
                         font=("Segoe UI", 28, "bold"),
                         text_color=accent_color).pack(anchor="w")
            ctk.CTkLabel(txt, text=label, font=FONT_BODY,
                         text_color=TEXT_PRI).pack(anchor="w")

            ctk.CTkFrame(c, fg_color=BORDER, height=1).pack(fill="x", padx=20)
            ctk.CTkLabel(c, text=sublabel, font=FONT_SMALL,
                         text_color=TEXT_SEC).pack(anchor="w", padx=20, pady=(6, 16))

        today_total = today_present + today_absent
        att_pct = f"{today_present/today_total*100:.0f}% present today" if today_total else "No records today"

        stat_card(cards_row, "👥", n_students,  "Students",    f"{n_enroll} total enrollments",   ACCENT)
        stat_card(cards_row, "📚", n_courses,   "Courses",     "Active this semester",             ACCENT2)
        stat_card(cards_row, "✅", today_present,"Present Today", att_pct,                         SUCCESS)
        stat_card(cards_row, "📷", today_scans, "Face Scans",  "Successful scans today",           WARNING)

        # ── Bottom two-column layout 
        bottom = ctk.CTkFrame(scroll, fg_color="transparent")
        bottom.pack(fill="both", expand=True, padx=28, pady=12)

        left_col  = ctk.CTkFrame(bottom, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right_col = ctk.CTkFrame(bottom, fg_color="transparent")
        right_col.pack(side="left", fill="both", expand=True, padx=(8, 0))

        # ── Left: Student attendance rates 
        lcard = ctk.CTkFrame(left_col, fg_color=CARD_BG, corner_radius=14,
                             border_width=1, border_color=BORDER)
        lcard.pack(fill="both", expand=True)
        lp = ctk.CTkFrame(lcard, fg_color="transparent")
        lp.pack(padx=20, pady=16, fill="both", expand=True)

        ctk.CTkLabel(lp, text="Student Attendance",
                     font=FONT_H3, text_color=TEXT_PRI).pack(anchor="w")
        ctk.CTkLabel(lp, text="Overall attendance rate per student",
                     font=FONT_SMALL, text_color=TEXT_SEC).pack(anchor="w", pady=(2, 14))

        for sr in student_rates:
            total   = sr["total"] or 0
            present = sr["present"] or 0
            pct     = (present / total) if total > 0 else 0
            pct_str = f"{pct*100:.0f}%" if total > 0 else "No data"
            bar_color = SUCCESS if pct >= 0.75 else (WARNING if pct >= 0.5 else DANGER)

            row_f = ctk.CTkFrame(lp, fg_color="transparent")
            row_f.pack(fill="x", pady=5)

            # Name + roll
            name_f = ctk.CTkFrame(row_f, fg_color="transparent", width=200)
            name_f.pack(side="left")
            name_f.pack_propagate(False)
            ctk.CTkLabel(name_f, text=sr["name"], font=FONT_BODY,
                         text_color=TEXT_PRI, anchor="w").pack(anchor="w")
            ctk.CTkLabel(name_f, text=sr["roll_number"], font=FONT_SMALL,
                         text_color=TEXT_SEC, anchor="w").pack(anchor="w")

            # Progress bar
            bar_outer = ctk.CTkFrame(row_f, fg_color="#1e2130",
                                     height=8, corner_radius=4)
            bar_outer.pack(side="left", fill="x", expand=True, padx=(12, 10))
            bar_outer.pack_propagate(False)
            bar_outer.update_idletasks()
            # Draw bar as a colored frame inside
            bar_pct_frame = ctk.CTkFrame(bar_outer,
                                         fg_color=bar_color,
                                         height=8, corner_radius=4)
            # We use place for proportional width
            bar_pct_frame.place(relx=0, rely=0, relwidth=max(pct, 0.02), relheight=1.0)

            # Percentage label
            ctk.CTkLabel(row_f, text=pct_str, font=FONT_SMALL,
                         text_color=bar_color, width=42, anchor="e").pack(side="left")

            # present/total
            ctk.CTkLabel(row_f, text=f"{present}/{total}",
                         font=FONT_SMALL, text_color=TEXT_SEC,
                         width=46, anchor="e").pack(side="left")

        # ── Right col: Course summary + recent activity 

        # Course summary card
        rcard_top = ctk.CTkFrame(right_col, fg_color=CARD_BG, corner_radius=14,
                                 border_width=1, border_color=BORDER)
        rcard_top.pack(fill="x", pady=(0, 12))
        rp = ctk.CTkFrame(rcard_top, fg_color="transparent")
        rp.pack(padx=20, pady=16, fill="x")

        ctk.CTkLabel(rp, text="Course Overview",
                     font=FONT_H3, text_color=TEXT_PRI).pack(anchor="w")
        ctk.CTkLabel(rp, text="Attendance rate per course",
                     font=FONT_SMALL, text_color=TEXT_SEC).pack(anchor="w", pady=(2, 14))

        for cr in course_rates:
            total   = cr["total"] or 0
            present = cr["present"] or 0
            pct     = (present / total * 100) if total > 0 else 0
            pct_str = f"{pct:.0f}%" if total > 0 else "—"
            bar_color = SUCCESS if pct >= 75 else (WARNING if pct >= 50 else DANGER)

            crow = ctk.CTkFrame(rp, fg_color="transparent")
            crow.pack(fill="x", pady=4)

            ctk.CTkLabel(crow, text=cr["course_code"],
                         font=("Segoe UI", 10, "bold"),
                         text_color=ACCENT, width=60, anchor="w").pack(side="left")
            ctk.CTkLabel(crow, text=cr["course_name"],
                         font=FONT_SMALL, text_color=TEXT_SEC,
                         width=180, anchor="w").pack(side="left", padx=(4, 12))

            bar_outer = ctk.CTkFrame(crow, fg_color="#1e2130",
                                     height=8, corner_radius=4)
            bar_outer.pack(side="left", fill="x", expand=True, padx=(0, 10))
            bar_outer.pack_propagate(False)
            bar_pct_frame = ctk.CTkFrame(bar_outer, fg_color=bar_color,
                                         height=8, corner_radius=4)
            bar_pct_frame.place(relx=0, rely=0, relwidth=max(pct/100, 0.02), relheight=1.0)

            ctk.CTkLabel(crow, text=pct_str, font=FONT_SMALL,
                         text_color=bar_color, width=36, anchor="e").pack(side="left")

        # Recent activity feed
        rcard_bot = ctk.CTkFrame(right_col, fg_color=CARD_BG, corner_radius=14,
                                 border_width=1, border_color=BORDER)
        rcard_bot.pack(fill="both", expand=True)
        rap = ctk.CTkFrame(rcard_bot, fg_color="transparent")
        rap.pack(padx=20, pady=16, fill="both", expand=True)

        ctk.CTkLabel(rap, text="Recent Activity",
                     font=FONT_H3, text_color=TEXT_PRI).pack(anchor="w")
        ctk.CTkLabel(rap, text="Latest attendance events",
                     font=FONT_SMALL, text_color=TEXT_SEC).pack(anchor="w", pady=(2, 14))

        for r in recent:
            is_present = r["status"] == "present"
            dot_color  = SUCCESS if is_present   else DANGER
            via_icon   = "📷" if r["marked_via"] == "face_id" else "✏️"
            time_str   = str(r["check_in_time"])[:5] if r["check_in_time"] else str(r["attendance_date"])

            item = ctk.CTkFrame(rap, fg_color="transparent")
            item.pack(fill="x", pady=3)

            # Colored dot
            dot = ctk.CTkFrame(item, fg_color=dot_color,
                               width=8, height=8, corner_radius=4)
            dot.pack(side="left", padx=(0, 10))
            dot.pack_propagate(False)

            ctk.CTkLabel(item, text=via_icon,
                         font=("Segoe UI", 11)).pack(side="left", padx=(0, 6))

            ctk.CTkLabel(item, text=r["student"],
                         font=("Segoe UI", 10, "bold"),
                         text_color=TEXT_PRI).pack(side="left")

            ctk.CTkLabel(item,
                         text=f"  {r['course_code']}  •  {'present' if is_present else 'absent'}",
                         font=FONT_SMALL, text_color=TEXT_SEC).pack(side="left")

            ctk.CTkLabel(item, text=time_str,
                         font=FONT_SMALL, text_color=TEXT_SEC).pack(side="right")

            # Divider
            ctk.CTkFrame(rap, fg_color=BORDER, height=1).pack(fill="x", pady=(3, 0))

    def _page_header_mini(self, text: str):
        ctk.CTkLabel(self._content, text=text, font=FONT_H3,
                     text_color=TEXT_PRI).pack(anchor="w", padx=32, pady=(16, 4))

    #  PAGE: Students
    def _page_students(self):
        self._page_header("Students", "All enrolled students — double-click a row to edit")

        try:
            conn = connect_pg()
            cur  = get_cursor(conn)
            cur.execute("""
                SELECT s.student_id, s.roll_number,
                       s.first_name, s.last_name,
                       s.first_name || ' ' || s.last_name AS name,
                       s.gender, s.phone, s.enrollment_year,
                       s.current_semester, s.date_of_birth, s.address,
                       CASE WHEN s.is_active THEN 'Active' ELSE 'Inactive' END AS status,
                       s.is_active,
                       u.email
                FROM students s
                JOIN users u USING (user_id)
                ORDER BY s.roll_number
            """)
            rows = cur.fetchall()
            conn.close()
        except Exception as e:
            show_error(f"DB error: {e}")
            return

        row_data: dict = {}

        cols = [
            ("id",       "ID",          55),
            ("roll",     "Roll No",     100),
            ("name",     "Full Name",   180),
            ("email",    "Email",       200),
            ("gender",   "Gender",       70),
            ("phone",    "Phone",       130),
            ("year",     "Enrol. Year", 100),
            ("semester", "Semester",     90),
            ("status",   "Status",       80),
        ]
        wrap = ctk.CTkFrame(self._content, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=32, pady=4)

        hint = ctk.CTkFrame(wrap, fg_color="transparent")
        hint.pack(anchor="e", pady=(0, 4))
        subtle_label(hint, "✏️  Double-click any row to edit").pack()

        tree = build_treeview(wrap, cols)

        for r in rows:
            iid = tree.insert("", "end", values=(
                r["student_id"], r["roll_number"], r["name"],
                r["email"],
                r["gender"] or "—", r["phone"] or "—",
                r["enrollment_year"] or "—", r["current_semester"] or "—",
                r["status"]
            ))
            row_data[iid] = dict(r)

        def on_double_click(event):
            item = tree.identify_row(event.y)
            if not item:
                return
            self._open_edit_student(row_data[item], refresh=lambda: self._show_page("students"))

        tree.bind("<Double-1>", on_double_click)

    def _open_edit_student(self, data: dict, refresh):
        """Pop-up window to edit a student record and persist to Postgres."""
        win = toplevel_window(f"Edit Student — {data['name']}", width=520, height=640)

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=16)

        ctk.CTkLabel(scroll, text=f"✏️  Editing: {data['name']}",
                     font=FONT_H2, text_color=TEXT_PRI).pack(anchor="w", pady=(0, 16))

        fields: dict = {}

        def add_field(label, key, value, show=""):
            field_label(scroll, label)
            e = entry(scroll, "", width=420, show=show)
            e.insert(0, value or "")
            e.pack(fill="x", pady=(2, 10))
            fields[key] = e

        add_field("Email",           "email",            data.get("email", ""))
        add_field("First Name",      "first_name",       data.get("first_name", ""))
        add_field("Last Name",       "last_name",        data.get("last_name", ""))
        add_field("Roll Number",     "roll_number",      data.get("roll_number", ""))
        add_field("Phone",           "phone",            data.get("phone", ""))
        add_field("Enrollment Year", "enrollment_year",  str(data.get("enrollment_year") or ""))
        add_field("Semester",        "current_semester", str(data.get("current_semester") or ""))
        add_field("Date of Birth",   "date_of_birth",    str(data.get("date_of_birth") or ""))
        add_field("Address",         "address",          data.get("address", ""))

        field_label(scroll, "Gender")
        gender_var = ctk.StringVar(value=data.get("gender") or "M")
        gr = ctk.CTkFrame(scroll, fg_color="transparent")
        gr.pack(fill="x", pady=(2, 10))
        for val, lbl in [("M", "Male"), ("F", "Female")]:
            ctk.CTkRadioButton(gr, text=lbl, variable=gender_var, value=val,
                               text_color=TEXT_PRI, fg_color=ACCENT,
                               font=FONT_BODY).pack(side="left", padx=(0, 12))

        field_label(scroll, "Status")
        active_var = ctk.BooleanVar(value=bool(data.get("is_active", True)))
        ctk.CTkSwitch(scroll, text="Active", variable=active_var,
                      onvalue=True, offvalue=False,
                      progress_color=SUCCESS, font=FONT_BODY,
                      text_color=TEXT_PRI).pack(anchor="w", pady=(2, 10))

        field_label(scroll, "New Password  (leave blank to keep current)")
        pw_entry = entry(scroll, "••••••••", width=420, show="*")
        pw_entry.pack(fill="x", pady=(2, 16))

        def save():
            try:
                conn = connect_pg()
                cur  = get_cursor(conn)

                cur.execute("""
                    UPDATE students SET
                        first_name       = %s,
                        last_name        = %s,
                        roll_number      = %s,
                        phone            = %s,
                        enrollment_year  = %s,
                        current_semester = %s,
                        date_of_birth    = %s,
                        address          = %s,
                        gender           = %s,
                        is_active        = %s
                    WHERE student_id = %s
                """, (
                    fields["first_name"].get().strip(),
                    fields["last_name"].get().strip(),
                    fields["roll_number"].get().strip(),
                    fields["phone"].get().strip() or None,
                    fields["enrollment_year"].get().strip() or None,
                    fields["current_semester"].get().strip() or None,
                    fields["date_of_birth"].get().strip() or None,
                    fields["address"].get().strip() or None,
                    gender_var.get(),
                    active_var.get(),
                    data["student_id"]
                ))

                new_email = fields["email"].get().strip()
                if new_email and new_email != data.get("email"):
                    cur.execute("""
                        UPDATE users SET email = %s
                        WHERE user_id = (SELECT user_id FROM students WHERE student_id = %s)
                    """, (new_email, data["student_id"]))

                new_pw = pw_entry.get()
                if new_pw.strip():
                    pw_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
                    cur.execute("""
                        UPDATE users SET password_hash = %s
                        WHERE user_id = (SELECT user_id FROM students WHERE student_id = %s)
                    """, (pw_hash, data["student_id"]))

                conn.commit()
                conn.close()
                show_info("Student record updated successfully.")
                win.destroy()
                refresh()

            except Exception as e:
                show_error(f"DB error:\n{e}")

        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", pady=(4, 8))
        styled_button(btn_row, "💾  Save Changes", save, width=200).pack(side="left")
        styled_button(btn_row, "Cancel", win.destroy,
                      color="#2a2d3e", width=100).pack(side="left", padx=(12, 0))

    #  PAGE: Courses
    def _page_courses(self):
        self._page_header("Courses", "Active courses and enrollments")

        try:
            conn = connect_pg()
            cur  = get_cursor(conn)
            cur.execute("""
                SELECT c.course_id, c.course_code, c.course_name, c.credits,
                       c.semester,
                       t.first_name || ' ' || t.last_name AS teacher,
                       COUNT(e.enrollment_id) AS enrolled,
                       CASE WHEN c.is_active THEN 'Active' ELSE 'Inactive' END AS status
                FROM courses c
                LEFT JOIN teachers   t USING (teacher_id)
                LEFT JOIN enrollments e USING (course_id)
                GROUP BY c.course_id, t.first_name, t.last_name
                ORDER BY c.course_code
            """)
            rows = cur.fetchall()
            conn.close()
        except Exception as e:
            show_error(f"DB error: {e}")
            return

        cols = [
            ("id",       "ID",           50),
            ("code",     "Code",         90),
            ("name",     "Course Name",  220),
            ("credits",  "Credits",      70),
            ("semester", "Semester",     120),
            ("teacher",  "Teacher",      160),
            ("enrolled", "Enrolled",     80),
            ("status",   "Status",       80),
        ]
        wrap = ctk.CTkFrame(self._content, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=32, pady=4)
        tree = build_treeview(wrap, cols)

        for r in rows:
            tree.insert("", "end", values=(
                r["course_id"], r["course_code"], r["course_name"],
                r["credits"], r["semester"] or "—", r["teacher"] or "—",
                r["enrolled"], r["status"]
            ))

    #  PAGE: Attendance sheet
    def _page_attendance(self):
        self._page_header("Attendance", "Color-coded attendance grid  —  click any cell to edit")

        # ── Filter bar 
        fb = card(self._content)
        fb.pack(fill="x", padx=32, pady=4)
        inner = ctk.CTkFrame(fb, fg_color="transparent")
        inner.pack(padx=20, pady=14, fill="x")

        ctk.CTkLabel(inner, text="Course:", font=FONT_BODY,
                     text_color=TEXT_SEC).grid(row=0, column=0, padx=(0, 6))

        try:
            conn = connect_pg()
            cur  = get_cursor(conn)
            cur.execute("SELECT course_id, course_code || ' — ' || course_name AS label FROM courses WHERE is_active ORDER BY course_code")
            courses = cur.fetchall()
            conn.close()
        except Exception:
            courses = []

        course_labels = ["All"] + [r["label"] for r in courses]
        course_ids    = [None]  + [r["course_id"] for r in courses]

        self._att_course_var = ctk.StringVar(value="All")
        cbox = combo(inner, course_labels, width=260)
        cbox.configure(variable=self._att_course_var)
        cbox.grid(row=0, column=1, padx=8)

        ctk.CTkLabel(inner, text="From:", font=FONT_BODY,
                     text_color=TEXT_SEC).grid(row=0, column=2, padx=(16, 6))
        self._att_from = entry(inner, "YYYY-MM-DD", width=130)
        self._att_from.grid(row=0, column=3, padx=4)

        ctk.CTkLabel(inner, text="To:", font=FONT_BODY,
                     text_color=TEXT_SEC).grid(row=0, column=4, padx=(8, 6))
        self._att_to = entry(inner, "YYYY-MM-DD", width=130)
        self._att_to.grid(row=0, column=5, padx=4)

        # Legend
        leg = ctk.CTkFrame(inner, fg_color="transparent")
        leg.grid(row=0, column=7, padx=(24, 0))
        for color, label in [("#1a3d2b", "Present"), ("#3d1a1a", "Absent"), ("#1e2130", "—")]:
            box = ctk.CTkFrame(leg, fg_color=color, width=14, height=14, corner_radius=3)
            box.pack(side="left", padx=(6, 2))
            ctk.CTkLabel(leg, text=label, font=FONT_SMALL,
                         text_color=TEXT_SEC).pack(side="left", padx=(0, 6))

        # ── Grid area 
        self._att_tree_frame = ctk.CTkFrame(self._content, fg_color="transparent")
        self._att_tree_frame.pack(fill="both", expand=True, padx=32, pady=4)

        def load_attendance():
            label     = self._att_course_var.get()
            cid_idx   = course_labels.index(label) if label in course_labels else 0
            cid       = course_ids[cid_idx]
            date_from = self._att_from.get().strip() or None
            date_to   = self._att_to.get().strip() or None

            for w in self._att_tree_frame.winfo_children():
                w.destroy()

            try:
                conn = connect_pg()
                cur  = get_cursor(conn)
                cur.execute("""
                    SELECT a.attendance_id,
                           s.student_id, s.roll_number,
                           s.first_name || ' ' || s.last_name AS student,
                           c.course_id, c.course_code,
                           a.attendance_date, a.status,
                           a.marked_via, a.check_in_time, a.remarks
                    FROM attendance a
                    JOIN students s USING (student_id)
                    JOIN courses  c USING (course_id)
                    WHERE (%s IS NULL OR c.course_id = %s)
                      AND (%s IS NULL OR a.attendance_date >= %s::date)
                      AND (%s IS NULL OR a.attendance_date <= %s::date)
                    ORDER BY s.roll_number, a.attendance_date
                """, (cid, cid, date_from, date_from, date_to, date_to))
                rows = cur.fetchall()
                conn.close()
            except Exception as e:
                show_error(f"DB error: {e}")
                return

            if not rows:
                ctk.CTkLabel(self._att_tree_frame,
                             text="No attendance records found for the selected filters.",
                             font=FONT_BODY, text_color=TEXT_SEC).pack(pady=40)
                return

            # ── Pivot: student → date → record 
            import collections
            # ordered list of unique dates (ascending) and students (by roll)
            dates    = sorted(set(str(r["attendance_date"]) for r in rows))
            students = []
            seen_s   = set()
            for r in rows:
                sid = r["student_id"]
                if sid not in seen_s:
                    students.append((sid, r["roll_number"], r["student"]))
                    seen_s.add(sid)

            # cell_data[(student_id, date_str)] = full row dict
            cell_data: dict = {}
            for r in rows:
                cell_data[(r["student_id"], str(r["attendance_date"]))] = dict(r)

            # ── Layout constants 
            ROW_H      = 36
            NAME_W     = 220   # student name column
            ROLL_W     = 90    # roll number column
            CELL_W     = 72    # each date column
            HEADER_H   = 52
            PAD        = 2     # gap between cells

            total_w = ROLL_W + NAME_W + len(dates) * (CELL_W + PAD) + 20
            total_h = HEADER_H + len(students) * (ROW_H + PAD) + 20

            # ── Scrollable canvas container 
            import tkinter as tk
            canvas_outer = tk.Frame(self._att_tree_frame, bg="#0f1117")
            canvas_outer.pack(fill="both", expand=True)

            canvas = tk.Canvas(canvas_outer, bg="#0f1117",
                               highlightthickness=0,
                               scrollregion=(0, 0, total_w, total_h))

            h_scroll = tk.Scrollbar(canvas_outer, orient="horizontal",
                                    command=canvas.xview)
            v_scroll = tk.Scrollbar(canvas_outer, orient="vertical",
                                    command=canvas.yview)
            canvas.configure(xscrollcommand=h_scroll.set,
                             yscrollcommand=v_scroll.set)

            h_scroll.pack(side="bottom", fill="x")
            v_scroll.pack(side="right",  fill="y")
            canvas.pack(side="left", fill="both", expand=True)

            # mousewheel scroll
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

            # ── Draw header row 
            x0 = 4
            # "Roll No" header
            canvas.create_rectangle(x0, 4, x0 + ROLL_W, HEADER_H,
                                    fill="#13151f", outline="#2d3148", width=1)
            canvas.create_text(x0 + ROLL_W // 2, HEADER_H // 2,
                               text="Roll No", fill="#94a3b8",
                               font=("Segoe UI", 9, "bold"))
            x0 += ROLL_W + PAD

            # "Student" header
            canvas.create_rectangle(x0, 4, x0 + NAME_W, HEADER_H,
                                    fill="#13151f", outline="#2d3148", width=1)
            canvas.create_text(x0 + NAME_W // 2, HEADER_H // 2,
                               text="Student", fill="#94a3b8",
                               font=("Segoe UI", 9, "bold"))
            x0 += NAME_W + PAD

            # Date headers
            for d in dates:
                # show as DD/MM to save space
                short = d[8:] + "/" + d[5:7]
                canvas.create_rectangle(x0, 4, x0 + CELL_W, HEADER_H,
                                        fill="#13151f", outline="#2d3148", width=1)
                canvas.create_text(x0 + CELL_W // 2, HEADER_H // 2 - 6,
                                   text=short, fill="#4f8ef7",
                                   font=("Segoe UI", 8, "bold"))
                # weekday label
                import datetime as dt
                try:
                    day_name = dt.date.fromisoformat(d).strftime("%a")
                except Exception:
                    day_name = ""
                canvas.create_text(x0 + CELL_W // 2, HEADER_H // 2 + 10,
                                   text=day_name, fill="#64748b",
                                   font=("Segoe UI", 7))
                x0 += CELL_W + PAD

            # ── Draw student rows 
            # Colors
            CLR_PRESENT_BG  = "#1a3d2b"
            CLR_PRESENT_FG  = "#4ade80"
            CLR_ABSENT_BG   = "#3d1a1a"
            CLR_ABSENT_FG   = "#f87171"
            CLR_NONE_BG     = "#1e2130"
            CLR_NONE_FG     = "#475569"
            CLR_ROW_ALT     = "#161928"   # alternate row tint

            for row_idx, (sid, roll, sname) in enumerate(students):
                y0     = HEADER_H + row_idx * (ROW_H + PAD)
                y1     = y0 + ROW_H
                row_bg = CLR_ROW_ALT if row_idx % 2 == 0 else "#0f1117"
                x0     = 4

                # Roll No cell
                canvas.create_rectangle(x0, y0, x0 + ROLL_W, y1,
                                        fill=row_bg, outline="#2d3148", width=1)
                canvas.create_text(x0 + ROLL_W // 2, (y0 + y1) // 2,
                                   text=roll, fill="#94a3b8",
                                   font=("Segoe UI", 9))
                x0 += ROLL_W + PAD

                # Student name cell
                canvas.create_rectangle(x0, y0, x0 + NAME_W, y1,
                                        fill=row_bg, outline="#2d3148", width=1)
                canvas.create_text(x0 + 10, (y0 + y1) // 2,
                                   text=sname, fill="#f1f5f9",
                                   font=("Segoe UI", 9), anchor="w")
                x0 += NAME_W + PAD

                # Status cells
                for d in dates:
                    rec = cell_data.get((sid, d))
                    if rec is None:
                        bg, fg, txt = CLR_NONE_BG, CLR_NONE_FG, "—"
                    elif rec["status"] == "present":
                        bg, fg, txt = CLR_PRESENT_BG, CLR_PRESENT_FG, "P"
                    else:
                        bg, fg, txt = CLR_ABSENT_BG, CLR_ABSENT_FG, "A"

                    rect_id = canvas.create_rectangle(
                        x0 + 1, y0 + 1, x0 + CELL_W - 1, y1 - 1,
                        fill=bg, outline="#2d3148", width=1,
                        tags=("cell",)
                    )
                    text_id = canvas.create_text(
                        x0 + CELL_W // 2, (y0 + y1) // 2,
                        text=txt, fill=fg,
                        font=("Segoe UI", 10, "bold"),
                        tags=("cell",)
                    )

                    # Click handler — open edit popup
                    if rec is not None:
                        def make_click_handler(record):
                            def handler(event):
                                self._open_edit_attendance(
                                    record, refresh=load_attendance
                                )
                            return handler

                        fn = make_click_handler(rec)
                        canvas.tag_bind(rect_id, "<Button-1>", fn)
                        canvas.tag_bind(text_id, "<Button-1>", fn)

                        # Hover highlight
                        def make_hover(rid, orig_bg, hover_bg="#2d3148"):
                            canvas.tag_bind(rid, "<Enter>",
                                lambda e, r=rid, hb=hover_bg: canvas.itemconfig(r, outline=hb, width=2))
                            canvas.tag_bind(rid, "<Leave>",
                                lambda e, r=rid, ob="#2d3148": canvas.itemconfig(r, outline=ob, width=1))
                        make_hover(rect_id, bg)

                    x0 += CELL_W + PAD

            # Summary bar — present % per student
            sum_y = HEADER_H + len(students) * (ROW_H + PAD) + 8
            x0 = 4
            canvas.create_rectangle(x0, sum_y, x0 + ROLL_W, sum_y + ROW_H,
                                    fill="#13151f", outline="#2d3148")
            canvas.create_text(x0 + ROLL_W // 2, sum_y + ROW_H // 2,
                               text="Total %", fill="#94a3b8",
                               font=("Segoe UI", 8, "bold"))
            x0 += ROLL_W + PAD

            canvas.create_rectangle(x0, sum_y, x0 + NAME_W, sum_y + ROW_H,
                                    fill="#13151f", outline="#2d3148")
            x0 += NAME_W + PAD

            for d in dates:
                present_count = sum(
                    1 for (s, dt2), rec in cell_data.items()
                    if dt2 == d and rec["status"] == "present"
                )
                total_count = sum(1 for (s, dt2) in cell_data if dt2 == d)
                pct = f"{present_count}/{total_count}" if total_count else "—"
                col = CLR_PRESENT_FG if present_count == total_count else (
                      CLR_ABSENT_FG  if present_count == 0 else "#f59e0b")
                canvas.create_rectangle(x0, sum_y, x0 + CELL_W, sum_y + ROW_H,
                                        fill="#13151f", outline="#2d3148")
                canvas.create_text(x0 + CELL_W // 2, sum_y + ROW_H // 2,
                                   text=pct, fill=col,
                                   font=("Segoe UI", 8, "bold"))
                x0 += CELL_W + PAD

            canvas.configure(scrollregion=(0, 0, total_w, sum_y + ROW_H + 10))

        styled_button(inner, "  🔍  Filter", load_attendance,
                      width=120).grid(row=0, column=6, padx=(16, 0))
        load_attendance()

    #  PAGE: Manual Attendance + Face ID
    def _page_manual_att(self):
        self._page_header("Mark Attendance",
                          "Submit manual records or launch Face-ID scanning")

        # Load data
        try:
            conn = connect_pg()
            cur  = get_cursor(conn)
            cur.execute("SELECT course_id, course_code || ' — ' || course_name AS label FROM courses WHERE is_active ORDER BY course_code")
            courses = cur.fetchall()
            cur.execute("SELECT student_id, roll_number || '  ' || first_name || ' ' || last_name AS label FROM students WHERE is_active ORDER BY roll_number")
            students = cur.fetchall()
            conn.close()
        except Exception as e:
            show_error(f"DB error: {e}")
            return

        if not courses:
            ctk.CTkLabel(self._content, text="No active courses found.",
                         text_color=DANGER, font=FONT_BODY).pack(padx=32, pady=20)
            return

        course_labels = [r["label"] for r in courses]
        course_ids    = [r["course_id"] for r in courses]
        student_labels= [r["label"] for r in students]
        student_ids   = [r["student_id"] for r in students]

        cols_outer = ctk.CTkFrame(self._content, fg_color="transparent")
        cols_outer.pack(fill="both", expand=True, padx=32, pady=8)

        # ── Manual form (left) 
        left = card(cols_outer)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        lp = ctk.CTkFrame(left, fg_color="transparent")
        lp.pack(padx=24, pady=20, fill="both")

        ctk.CTkLabel(lp, text="✏️  Manual Entry", font=FONT_H2,
                     text_color=TEXT_PRI).pack(anchor="w", pady=(0, 16))

        field_label(lp, "Course")
        self._man_course = combo(lp, course_labels)
        self._man_course.pack(fill="x", pady=(2, 10))

        field_label(lp, "Student")
        self._man_student = combo(lp, student_labels)
        self._man_student.pack(fill="x", pady=(2, 10))

        field_label(lp, "Date (YYYY-MM-DD)")
        self._man_date = entry(lp, str(datetime.date.today()))
        self._man_date.insert(0, str(datetime.date.today()))
        self._man_date.pack(fill="x", pady=(2, 10))

        field_label(lp, "Status")
        self._man_status = combo(lp, ["present", "absent"])
        self._man_status.pack(fill="x", pady=(2, 10))

        field_label(lp, "Remarks (optional)")
        self._man_remarks = entry(lp, "e.g. Medical leave")
        self._man_remarks.pack(fill="x", pady=(2, 10))

        def save_manual():
            cidx    = course_labels.index(self._man_course.get())
            sidx    = student_labels.index(self._man_student.get())
            cid     = course_ids[cidx]
            sid     = student_ids[sidx]
            date    = self._man_date.get().strip()
            status  = self._man_status.get()
            remarks = self._man_remarks.get().strip() or None

            try:
                conn = connect_pg()
                cur  = get_cursor(conn)
                cur.execute("""
                    INSERT INTO attendance
                        (student_id, course_id, attendance_date,
                         status, marked_by, marked_via, remarks)
                    VALUES (%s, %s, %s, %s, %s, 'manual', %s)
                    ON CONFLICT (student_id, course_id, attendance_date)
                    DO UPDATE SET status     = EXCLUDED.status,
                                  marked_via = 'manual',
                                  remarks    = EXCLUDED.remarks,
                                  marked_by  = EXCLUDED.marked_by
                    RETURNING attendance_id
                """, (sid, cid, date, status, self.user_id, remarks))
                att_row = cur.fetchone()
                att_id  = att_row["attendance_id"] if att_row else None
                log_access(conn, self.user_id, "manual_attendance",
                           "attendance", att_id)
                conn.commit()
                conn.close()
                show_info("Attendance recorded successfully.")
            except Exception as e:
                show_error(f"DB error: {e}")

        styled_button(lp, "💾  Save Record", save_manual, width=280).pack(pady=(12, 0))

        # ── Face-ID panel (right) ───────────
        right = card(cols_outer)
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))
        rp = ctk.CTkFrame(right, fg_color="transparent")
        rp.pack(padx=24, pady=20, fill="both")

        ctk.CTkLabel(rp, text="📷  Face-ID Scanning", font=FONT_H2,
                     text_color=TEXT_PRI).pack(anchor="w", pady=(0, 16))

        field_label(rp, "Course to mark")
        self._yolo_course = combo(rp, course_labels)
        self._yolo_course.pack(fill="x", pady=(2, 10))

        field_label(rp, "Date (YYYY-MM-DD)")
        self._yolo_date = entry(rp, str(datetime.date.today()))
        self._yolo_date.insert(0, str(datetime.date.today()))
        self._yolo_date.pack(fill="x", pady=(2, 10))

        self._yolo_status = ctk.CTkTextbox(rp, height=160, font=FONT_MONO,
                                            fg_color="#0f1117",
                                            text_color=SUCCESS)
        self._yolo_status.pack(fill="x", pady=(10, 10))
        self._yolo_status.insert("end", "Face-ID scanner ready.\n")
        self._yolo_status.configure(state="disabled")

        def append_status(msg: str):
            self._yolo_status.configure(state="normal")
            self._yolo_status.insert("end", msg + "\n")
            self._yolo_status.see("end")
            self._yolo_status.configure(state="disabled")

        def launch_yolo():
            cidx = course_labels.index(self._yolo_course.get())
            cid  = course_ids[cidx]
            date = self._yolo_date.get().strip()
            threading.Thread(
                target=run_yolo,
                args=(date, cid, self.user_id, append_status),
                daemon=True
            ).start()
            append_status("🚀  Launching camera…")

        styled_button(rp, "🚀  Start Face-ID", launch_yolo,
                      color=ACCENT2, width=280).pack(pady=(4, 0))

        subtle_label(rp,
            "Press Q in the camera window to stop scanning."
        ).pack(pady=(8, 0))

    #  PAGE: Marks
    def _page_marks(self):
        self._page_header("Marks", "View and edit student assessment scores")

        # Filter
        fb = card(self._content)
        fb.pack(fill="x", padx=32, pady=4)
        inner = ctk.CTkFrame(fb, fg_color="transparent")
        inner.pack(padx=20, pady=14, fill="x")

        ctk.CTkLabel(inner, text="Course:", font=FONT_BODY,
                     text_color=TEXT_SEC).grid(row=0, column=0, padx=(0,6))

        try:
            conn = connect_pg()
            cur  = get_cursor(conn)
            cur.execute("SELECT course_id, course_code || ' — ' || course_name AS label FROM courses WHERE is_active ORDER BY course_code")
            courses = cur.fetchall()
            conn.close()
        except Exception:
            courses = []

        course_labels = ["All"] + [r["label"] for r in courses]
        course_ids    = [None]  + [r["course_id"] for r in courses]

        self._marks_course_var = ctk.StringVar(value="All")
        cbox = combo(inner, course_labels, width=280)
        cbox.configure(variable=self._marks_course_var)
        cbox.grid(row=0, column=1, padx=8)

        self._marks_tree_frame = ctk.CTkFrame(self._content, fg_color="transparent")
        self._marks_tree_frame.pack(fill="both", expand=True, padx=32, pady=4)

        def load_marks():
            label   = self._marks_course_var.get()
            cid_idx = course_labels.index(label) if label in course_labels else 0
            cid     = course_ids[cid_idx]

            for w in self._marks_tree_frame.winfo_children():
                w.destroy()

            try:
                conn = connect_pg()
                cur  = get_cursor(conn)
                cur.execute("""
                    SELECT m.mark_id, m.student_id, m.assessment_id,
                           s.roll_number,
                           s.first_name || ' ' || s.last_name AS student,
                           c.course_code,
                           asm.title AS assessment,
                           at2.type_name AS type,
                           m.score, asm.max_score, m.remarks,
                           m.updated_at
                    FROM marks m
                    JOIN students        s   USING (student_id)
                    JOIN assessments     asm USING (assessment_id)
                    JOIN courses         c   USING (course_id)
                    JOIN assessment_types at2 ON asm.type_id = at2.type_id
                    WHERE (%s IS NULL OR c.course_id = %s)
                    ORDER BY s.roll_number, asm.assessment_date
                """, (cid, cid))
                rows = cur.fetchall()
                conn.close()
            except Exception as e:
                show_error(f"DB error: {e}")
                return

            cols = [
                ("roll",       "Roll No",    100),
                ("student",    "Student",    180),
                ("course",     "Course",     100),
                ("assessment", "Assessment", 120),
                ("type",       "Type",        90),
                ("score",      "Score",       70),
                ("max",        "Max",         60),
                ("pct",        "%",           60),
                ("remarks",    "Remarks",    160),
            ]
            hint_row = ctk.CTkFrame(self._marks_tree_frame, fg_color="transparent")
            hint_row.pack(anchor="e", pady=(0, 4))
            subtle_label(hint_row, "✏️  Double-click any row to edit").pack()

            tree = build_treeview(self._marks_tree_frame, cols, height=15)
            marks_row_data: dict = {}

            for r in rows:
                pct = f"{r['score']/r['max_score']*100:.0f}%" if r["max_score"] else "—"
                iid = tree.insert("", "end", values=(
                    r["roll_number"], r["student"], r["course_code"],
                    r["assessment"], r["type"],
                    r["score"], r["max_score"], pct,
                    r["remarks"] or "—"
                ))
                marks_row_data[iid] = dict(r)

            def on_marks_double_click(event, _tree=tree, _data=marks_row_data):
                item = _tree.identify_row(event.y)
                if not item:
                    return
                self._open_edit_marks(_data[item], refresh=load_marks)

            tree.bind("<Double-1>", on_marks_double_click)

        styled_button(inner, "  🔍  Filter", load_marks,
                      width=120).grid(row=0, column=2, padx=(16, 0))
        load_marks()

    #  PAGE: Add Student
    def _page_add_student(self):
        self._page_header("Add Student",
                          "Register a new student and create their login")

        # Scrollable container so the button is always reachable
        scroll = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=32, pady=8)

        outer = ctk.CTkFrame(scroll, fg_color="transparent")
        outer.pack(fill="both", expand=True)

        f = card(outer)
        f.pack(side="left", fill="y")
        fp = ctk.CTkFrame(f, fg_color="transparent")
        fp.pack(padx=30, pady=24, fill="x")

        ctk.CTkLabel(fp, text="Student Details", font=FONT_H2,
                     text_color=TEXT_PRI).pack(anchor="w", pady=(0,16))

        fields: dict[str, ctk.CTkEntry] = {}

        def add_field(label: str, placeholder: str, key: str, show=""):
            field_label(fp, label)
            e = entry(fp, placeholder, show=show)
            e.pack(fill="x", pady=(2, 10))
            fields[key] = e

        add_field("Email",            "student@giki.edu.pk", "email")
        add_field("Password",         "Temporary password",   "password", show="*")
        add_field("First Name",       "Muhammad",             "first_name")
        add_field("Last Name",        "Ali",                  "last_name")
        add_field("Roll Number",      "2024XXX",              "roll_number")
        add_field("Phone",            "03XXXXXXXXX",          "phone")
        add_field("Enrollment Year",  "2024",                 "enrollment_year")
        add_field("Semester",         "1",                    "current_semester")

        field_label(fp, "Date of Birth")
        dob = entry(fp, "YYYY-MM-DD")
        dob.pack(fill="x", pady=(2, 10))
        fields["dob"] = dob

        field_label(fp, "Gender")
        gender_var = ctk.StringVar(value="M")
        gr = ctk.CTkFrame(fp, fg_color="transparent")
        gr.pack(fill="x", pady=(2, 10))
        for val, lbl in [("M", "Male"), ("F", "Female")]:
            ctk.CTkRadioButton(gr, text=lbl, variable=gender_var, value=val,
                               text_color=TEXT_PRI, fg_color=ACCENT,
                               font=FONT_BODY).pack(side="left", padx=(0, 12))

        def save_student():
            required = ["email", "password", "first_name", "last_name", "roll_number"]
            for k in required:
                if not fields[k].get().strip():
                    show_error(f"'{k}' is required.")
                    return

            email    = fields["email"].get().strip()
            password = fields["password"].get()
            fname    = fields["first_name"].get().strip()
            lname    = fields["last_name"].get().strip()
            roll     = fields["roll_number"].get().strip()
            phone    = fields["phone"].get().strip() or None
            enr_year = fields["enrollment_year"].get().strip() or None
            semester = fields["current_semester"].get().strip() or None
            dob_val  = fields["dob"].get().strip() or None
            gender   = gender_var.get()

            pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

            try:
                conn = connect_pg()
                cur  = get_cursor(conn)

                cur.execute("""
                    INSERT INTO users (email, password_hash, role)
                    VALUES (%s, %s, 'student')
                    RETURNING user_id
                """, (email, pw_hash))
                user_id = cur.fetchone()["user_id"]

                cur.execute("""
                    INSERT INTO students
                        (user_id, first_name, last_name, roll_number,
                         date_of_birth, gender, phone,
                         enrollment_year, current_semester)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (user_id, fname, lname, roll,
                      dob_val, gender, phone,
                      enr_year, semester))

                conn.commit()
                conn.close()
                show_info(f"Student '{fname} {lname}' added successfully.\nLogin: {email}")

                # Clear fields
                for e in fields.values():
                    e.delete(0, "end")

            except Exception as e:
                show_error(f"DB error:\n{e}")

        styled_button(fp, "➕  Add Student", save_student,
                      width=300).pack(pady=(8, 0))

    #  POPUP: Edit Attendance
    def _open_edit_attendance(self, data: dict, refresh):
        student_name = data.get("student", "")
        date_str     = str(data.get("attendance_date", ""))
        course       = data.get("course_code", "")
        att_id       = data.get("attendance_id")

        win = toplevel_window(
            f"Edit Attendance — {student_name}  •  {course}  •  {date_str}",
            width=460, height=360
        )

        fp = ctk.CTkFrame(win, fg_color="transparent")
        fp.pack(padx=32, pady=24, fill="both", expand=True)

        ctk.CTkLabel(fp, text="✏️  Edit Attendance Record",
                     font=FONT_H2, text_color=TEXT_PRI).pack(anchor="w", pady=(0, 4))
        subtle_label(fp,
            f"{student_name}  ·  {course}  ·  {date_str}"
        ).pack(anchor="w", pady=(0, 18))

        field_label(fp, "Status")
        status_var = ctk.StringVar(value=data.get("status", "present"))
        sr = ctk.CTkFrame(fp, fg_color="transparent")
        sr.pack(fill="x", pady=(2, 14))
        for val, lbl, color in [("present", "Present", SUCCESS), ("absent", "Absent", DANGER)]:
            ctk.CTkRadioButton(
                sr, text=lbl, variable=status_var, value=val,
                text_color=TEXT_PRI, fg_color=color, font=FONT_BODY
            ).pack(side="left", padx=(0, 20))

        field_label(fp, "Remarks")
        remarks_entry = entry(fp, "Optional note...", width=380)
        remarks_entry.insert(0, data.get("remarks") or "")
        remarks_entry.pack(fill="x", pady=(2, 20))

        def save():
            new_status  = status_var.get()
            new_remarks = remarks_entry.get().strip() or None
            try:
                conn = connect_pg()
                cur  = get_cursor(conn)
                cur.execute("""
                    UPDATE attendance
                    SET status     = %s,
                        remarks    = %s,
                        marked_via = 'manual',
                        marked_by  = %s
                    WHERE attendance_id = %s
                """, (new_status, new_remarks, self.user_id, att_id))
                log_access(conn, self.user_id, "edit_attendance",
                           "attendance", att_id)
                conn.commit()
                conn.close()
                show_info("Attendance updated successfully.")
                win.destroy()
                refresh()
            except Exception as e:
                show_error(f"DB error: {e}")

        btn_row = ctk.CTkFrame(fp, fg_color="transparent")
        btn_row.pack(fill="x")
        styled_button(btn_row, "Save Changes", save, width=180).pack(side="left")
        styled_button(btn_row, "Cancel", win.destroy,
                      color="#2d3148", width=100).pack(side="left", padx=(12, 0))

    #  POPUP: Edit Marks
    def _open_edit_marks(self, data: dict, refresh):
        student_name  = data.get("student", "")
        assessment    = data.get("assessment", "")
        course        = data.get("course_code", "")
        mark_id       = data.get("mark_id")
        max_score     = data.get("max_score", 100)

        win = toplevel_window(
            f"Edit Mark — {student_name}  •  {assessment}",
            width=460, height=340
        )

        fp = ctk.CTkFrame(win, fg_color="transparent")
        fp.pack(padx=32, pady=24, fill="both", expand=True)

        ctk.CTkLabel(fp, text="Edit Mark",
                     font=FONT_H2, text_color=TEXT_PRI).pack(anchor="w", pady=(0, 4))
        subtle_label(fp,
            f"{student_name}  |  {course}  |  {assessment}  (max: {max_score})"
        ).pack(anchor="w", pady=(0, 18))

        field_label(fp, f"Score  (0 to {max_score})")
        score_entry = entry(fp, "0.00", width=380)
        score_entry.insert(0, str(data.get("score", "")))
        score_entry.pack(fill="x", pady=(2, 14))

        field_label(fp, "Remarks")
        remarks_entry = entry(fp, "Optional note...", width=380)
        remarks_entry.insert(0, data.get("remarks") or "")
        remarks_entry.pack(fill="x", pady=(2, 20))

        def save():
            try:
                new_score = float(score_entry.get().strip())
            except ValueError:
                show_error("Score must be a number.")
                return
            if new_score < 0 or new_score > max_score:
                show_error(f"Score must be between 0 and {max_score}.")
                return

            new_remarks = remarks_entry.get().strip() or None
            try:
                conn = connect_pg()
                cur  = get_cursor(conn)
                cur.execute("""
                    UPDATE marks
                    SET score      = %s,
                        remarks    = %s,
                        updated_by = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE mark_id = %s
                """, (new_score, new_remarks, self.user_id, mark_id))
                log_access(conn, self.user_id, "edit_mark", "marks", mark_id)
                conn.commit()
                conn.close()
                show_info("Mark updated successfully.")
                win.destroy()
                refresh()
            except Exception as e:
                show_error(f"DB error: {e}")

        btn_row = ctk.CTkFrame(fp, fg_color="transparent")
        btn_row.pack(fill="x")
        styled_button(btn_row, "Save Changes", save, width=180).pack(side="left")
        styled_button(btn_row, "Cancel", win.destroy,
                      color="#2d3148", width=100).pack(side="left", padx=(12, 0))


#  Student Portal (read-only)

class StudentPortal(ctk.CTk):
    def __init__(self, user_id: int, email: str):
        super().__init__()
        self.user_id = user_id
        self.email   = email
        self.title("Student Record System — Student Portal")
        self.geometry("1100x720")
        self.configure(fg_color=DARK_BG)
        self._build_ui()
        self.mainloop()

    def _build_ui(self):
        # Get student_id
        try:
            conn = connect_pg()
            cur  = get_cursor(conn)
            cur.execute("SELECT student_id, first_name, last_name FROM students WHERE user_id = %s", (self.user_id,))
            row = cur.fetchone()
            conn.close()
        except Exception as e:
            show_error(f"DB error: {e}")
            self.destroy()
            return

        if row is None:
            show_error("No student profile found for this account.")
            self.destroy()
            return

        self.student_id   = row["student_id"]
        self.student_name = row["first_name"] + " " + row["last_name"]

        # Header
        hdr = ctk.CTkFrame(self, fg_color=SIDEBAR_BG, height=70, corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text=f"🎓  {self.student_name}",
                     font=FONT_H1, text_color=TEXT_PRI).pack(side="left", padx=28, pady=16)
        ctk.CTkLabel(hdr, text="Student Portal  •  Read-only",
                     font=FONT_SMALL, text_color=TEXT_SEC).pack(side="left")
        styled_button(hdr, "Logout", self._logout,
                      color="#1e2130", width=90).pack(side="right", padx=20)

        # Tabs
        tabs = ctk.CTkTabview(self, fg_color=DARK_BG,
                              segmented_button_fg_color=SIDEBAR_BG,
                              segmented_button_selected_color=ACCENT)
        tabs.pack(fill="both", expand=True, padx=20, pady=12)

        for tab in ["📋 Attendance", "📊 Marks"]:
            tabs.add(tab)

        self._build_attendance_tab(tabs.tab("📋 Attendance"))
        self._build_marks_tab(tabs.tab("📊 Marks"))

    def _logout(self):
        self.destroy()
        LoginApp().mainloop()

    def _build_attendance_tab(self, parent):
        import tkinter as tk
        import collections

        try:
            conn = connect_pg()
            cur  = get_cursor(conn)
            cur.execute("""
                SELECT c.course_id, c.course_code, c.course_name,
                       a.attendance_date, a.status, a.check_in_time
                FROM attendance a
                JOIN courses c USING (course_id)
                WHERE a.student_id = %s
                ORDER BY a.attendance_date
            """, (self.student_id,))
            rows = cur.fetchall()
            conn.close()
        except Exception as e:
            show_error(f"DB error: {e}")
            return

        total   = len(rows)
        present = sum(1 for r in rows if r["status"] == "present")
        absent  = total - present
        pct_val = (present / total) if total else 0
        pct_str = f"{pct_val*100:.1f}%" if total else "—"
        bar_color = SUCCESS if pct_val >= 0.75 else (WARNING if pct_val >= 0.5 else DANGER)

        # ── Summary cards 
        summary = card(parent)
        summary.pack(fill="x", padx=20, pady=(14, 8))
        sp = ctk.CTkFrame(summary, fg_color="transparent")
        sp.pack(padx=20, pady=16, fill="x")

        for lbl, val, color in [
            ("Total Classes", total,   TEXT_PRI),
            ("Present",       present, SUCCESS),
            ("Absent",        absent,  DANGER),
            ("Attendance",    pct_str, bar_color),
        ]:
            box = ctk.CTkFrame(sp, fg_color="#1e2130", corner_radius=10)
            box.pack(side="left", expand=True, fill="both", padx=6)
            ctk.CTkLabel(box, text=str(val),
                         font=("Segoe UI", 26, "bold"),
                         text_color=color).pack(pady=(14, 2))
            ctk.CTkLabel(box, text=lbl, font=FONT_SMALL,
                         text_color=TEXT_SEC).pack(pady=(0, 14))

        # Overall progress bar
        bar_wrap = ctk.CTkFrame(parent, fg_color="transparent")
        bar_wrap.pack(fill="x", padx=20, pady=(0, 10))
        bar_outer = ctk.CTkFrame(bar_wrap, fg_color="#1e2130", height=10, corner_radius=5)
        bar_outer.pack(fill="x")
        bar_outer.pack_propagate(False)
        bar_fill = ctk.CTkFrame(bar_outer, fg_color=bar_color, height=10, corner_radius=5)
        bar_fill.place(relx=0, rely=0, relwidth=max(pct_val, 0.02), relheight=1.0)

        if not rows:
            ctk.CTkLabel(parent, text="No attendance records yet.",
                         font=FONT_BODY, text_color=TEXT_SEC).pack(pady=30)
            return

        # ── Per-course color grid 
        # Group by course
        courses_seen = []
        course_map: dict = {}
        for r in rows:
            cid = r["course_id"]
            if cid not in course_map:
                course_map[cid] = {"code": r["course_code"], "name": r["course_name"], "rows": []}
                courses_seen.append(cid)
            course_map[cid]["rows"].append(r)

        # label
        ctk.CTkLabel(parent, text="Attendance by Course",
                     font=FONT_H3, text_color=TEXT_PRI).pack(anchor="w", padx=20, pady=(8, 4))
        subtle_label(parent, "Each cell = one class day   •   P = Present   A = Absent").pack(anchor="w", padx=20, pady=(0, 8))

        scroll_area = ctk.CTkScrollableFrame(parent, fg_color="transparent", height=340)
        scroll_area.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        ROW_H  = 34
        CELL_W = 58
        LABEL_W = 200
        PAD    = 2
        HEADER_H = 44

        CLR_P_BG = "#1a3d2b"; CLR_P_FG = "#4ade80"
        CLR_A_BG = "#3d1a1a"; CLR_A_FG = "#f87171"

        import datetime as _dt

        for cid in courses_seen:
            cdata = course_map[cid]
            dates = sorted(set(str(r["attendance_date"]) for r in cdata["rows"]))
            c_present = sum(1 for r in cdata["rows"] if r["status"] == "present")
            c_total   = len(cdata["rows"])
            c_pct     = f"{c_present/c_total*100:.0f}%" if c_total else "—"
            c_bar_col = SUCCESS if (c_present/c_total >= 0.75 if c_total else False) else (
                        WARNING if (c_present/c_total >= 0.5 if c_total else False) else DANGER)

            # Course header
            ch = ctk.CTkFrame(scroll_area, fg_color="#161928", corner_radius=8)
            ch.pack(fill="x", pady=(8, 2))
            chp = ctk.CTkFrame(ch, fg_color="transparent")
            chp.pack(padx=14, pady=8, fill="x")
            ctk.CTkLabel(chp, text=cdata["code"],
                         font=("Segoe UI", 11, "bold"), text_color=ACCENT).pack(side="left")
            ctk.CTkLabel(chp, text=f"  {cdata['name']}",
                         font=FONT_SMALL, text_color=TEXT_SEC).pack(side="left")
            ctk.CTkLabel(chp, text=f"{c_present}/{c_total}  •  {c_pct}",
                         font=("Segoe UI", 10, "bold"),
                         text_color=c_bar_col).pack(side="right")

            # Build date→record lookup
            date_rec = {str(r["attendance_date"]): r for r in cdata["rows"]}

            total_w = LABEL_W + len(dates) * (CELL_W + PAD) + 20
            canvas_h = HEADER_H + ROW_H + PAD + ROW_H + 8

            canvas_frame = tk.Frame(scroll_area._parent_canvas if hasattr(scroll_area, "_parent_canvas") else scroll_area, bg="#0f1117")
            canvas_frame.pack(fill="x", pady=2)

            canvas = tk.Canvas(canvas_frame, bg="#0f1117", highlightthickness=0,
                               height=canvas_h, width=total_w)
            hbar = tk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
            canvas.configure(xscrollcommand=hbar.set,
                             scrollregion=(0, 0, total_w, canvas_h))
            hbar.pack(side="bottom", fill="x")
            canvas.pack(fill="x")

            # Header: date labels
            x = LABEL_W + PAD
            for d in dates:
                short = d[8:] + "/" + d[5:7]
                try:
                    day = _dt.date.fromisoformat(d).strftime("%a")
                except Exception:
                    day = ""
                canvas.create_rectangle(x, 0, x + CELL_W, HEADER_H,
                                        fill="#13151f", outline="#2d3148")
                canvas.create_text(x + CELL_W//2, HEADER_H//2 - 7,
                                   text=short, fill="#4f8ef7",
                                   font=("Segoe UI", 8, "bold"))
                canvas.create_text(x + CELL_W//2, HEADER_H//2 + 8,
                                   text=day, fill="#64748b",
                                   font=("Segoe UI", 7))
                x += CELL_W + PAD

            # Row label
            y = HEADER_H
            canvas.create_rectangle(0, y, LABEL_W, y + ROW_H,
                                    fill="#161928", outline="#2d3148")
            canvas.create_text(12, y + ROW_H//2,
                               text="Attendance", fill="#94a3b8",
                               font=("Segoe UI", 9), anchor="w")

            # Status cells
            x = LABEL_W + PAD
            for d in dates:
                rec = date_rec.get(d)
                if rec and rec["status"] == "present":
                    bg, fg, txt = CLR_P_BG, CLR_P_FG, "P"
                elif rec and rec["status"] == "absent":
                    bg, fg, txt = CLR_A_BG, CLR_A_FG, "A"
                else:
                    bg, fg, txt = "#1e2130", "#475569", "—"

                canvas.create_rectangle(x+1, y+1, x+CELL_W-1, y+ROW_H-1,
                                        fill=bg, outline="#2d3148")
                canvas.create_text(x + CELL_W//2, y + ROW_H//2,
                                   text=txt, fill=fg,
                                   font=("Segoe UI", 10, "bold"))
                x += CELL_W + PAD

    def _build_marks_tab(self, parent):
        try:
            conn = connect_pg()
            cur  = get_cursor(conn)
            cur.execute("""
                SELECT c.course_code, c.course_name,
                       asm.title AS assessment,
                       at2.type_name AS type,
                       m.score, asm.max_score, m.remarks
                FROM marks m
                JOIN assessments      asm  USING (assessment_id)
                JOIN courses          c    USING (course_id)
                JOIN assessment_types at2  ON asm.type_id = at2.type_id
                WHERE m.student_id = %s AND asm.is_published
                ORDER BY c.course_code, asm.assessment_date
            """, (self.student_id,))
            rows = cur.fetchall()
            conn.close()
        except Exception as e:
            show_error(f"DB error: {e}")
            return

        cols = [
            ("course_code", "Course",    110),
            ("course_name", "Name",      200),
            ("assessment",  "Assessment",140),
            ("type",        "Type",       90),
            ("score",       "Score",      70),
            ("max",         "Max",        60),
            ("pct",         "%",          60),
            ("remarks",     "Remarks",   180),
        ]
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=20, pady=12)
        tree = build_treeview(wrap, cols, height=16)

        for r in rows:
            pct = f"{r['score']/r['max_score']*100:.0f}%" if r["max_score"] else "—"
            tree.insert("", "end", values=(
                r["course_code"], r["course_name"],
                r["assessment"], r["type"],
                r["score"], r["max_score"], pct,
                r["remarks"] or "—"
            ))


#  Entry point
if __name__ == "__main__":
    app = LoginApp()
    app.mainloop()
