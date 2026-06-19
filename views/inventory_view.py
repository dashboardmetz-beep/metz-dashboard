"""
Inventory Management — Track stock items, daily counts, waste, and purchase orders.
Connects to Food Cost data for cost analysis.
"""

from datetime import date, timedelta, datetime
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import DEPARTMENTS
from styles import page_header, dash_kpi_card, dash_chart_start, dash_chart_end, dash_section_header, hero_header
import db


# ─── Plotly theme (reuse from dashboard) ───
_THEME = dict(
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=13, color="#64748B"),
    margin=dict(l=10, r=10, t=10, b=10),
    hoverlabel=dict(bgcolor="#1F2A44", font_size=12, font_color="#FFFFFF"),
)


def _init_inventory_tables(conn):
    """Create inventory tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS inventory_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            unit TEXT DEFAULT 'each',
            unit_cost REAL DEFAULT 0.0,
            par_level REAL DEFAULT 0.0,
            supplier TEXT DEFAULT '',
            department TEXT DEFAULT 'Board & Catering',
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(name, department)
        );

        CREATE TABLE IF NOT EXISTS inventory_counts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            count_date TEXT NOT NULL,
            quantity REAL DEFAULT 0.0,
            counted_by TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (item_id) REFERENCES inventory_items(id),
            UNIQUE(item_id, count_date)
        );

        CREATE TABLE IF NOT EXISTS inventory_waste (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            waste_date TEXT NOT NULL,
            quantity REAL DEFAULT 0.0,
            reason TEXT DEFAULT '',
            cost REAL DEFAULT 0.0,
            department TEXT DEFAULT 'Board & Catering',
            logged_by TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier TEXT NOT NULL,
            order_date TEXT NOT NULL,
            delivery_date TEXT,
            department TEXT DEFAULT 'Board & Catering',
            status TEXT DEFAULT 'draft',
            total_cost REAL DEFAULT 0.0,
            notes TEXT DEFAULT '',
            created_by TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS po_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id INTEGER NOT NULL,
            item_id INTEGER,
            item_name TEXT NOT NULL,
            quantity REAL DEFAULT 0.0,
            unit_cost REAL DEFAULT 0.0,
            total_cost REAL DEFAULT 0.0,
            FOREIGN KEY (po_id) REFERENCES purchase_orders(id),
            FOREIGN KEY (item_id) REFERENCES inventory_items(id)
        );
    """)
    conn.commit()


# ─── Categories ───
_CATEGORIES = [
    "Proteins", "Dairy", "Produce", "Bakery", "Dry Goods",
    "Beverages", "Frozen", "Paper/Supplies", "Cleaning", "Other",
]

_UNITS = ["each", "lb", "oz", "case", "gallon", "bag", "box", "can", "dozen"]


def render(conn, user):
    """Main inventory page."""
    _init_inventory_tables(conn)

    hero_header("Inventory Management", "Track stock, waste, and purchase orders")

    sub = st.session_state.get("current_subsection", "Inventory")

    # Tabs within inventory
    tab1, tab2, tab3, tab4 = st.tabs([
        "Stock Items", "Daily Count", "Waste Log", "Purchase Orders"
    ])

    with tab1:
        _render_stock_items(conn, user)

    with tab2:
        _render_daily_count(conn, user)

    with tab3:
        _render_waste_log(conn, user)

    with tab4:
        _render_purchase_orders(conn, user)


def _render_stock_items(conn, user):
    """Manage inventory items — add, edit, view."""
    dept = st.selectbox(
        "Department", DEPARTMENTS + ["All"],
        index=0, key="inv_dept",
    )

    # Fetch items
    if dept == "All":
        items = conn.execute(
            "SELECT * FROM inventory_items WHERE active=1 ORDER BY category, name"
        ).fetchall()
    else:
        items = conn.execute(
            "SELECT * FROM inventory_items WHERE active=1 AND department=? ORDER BY category, name",
            (dept,)
        ).fetchall()

    # KPI row
    total_items = len(items)
    total_value = sum(
        (r["quantity"] if r["quantity"] else 0) * (r["unit_cost"] if r["unit_cost"] else 0)
        for r in items
    ) if items else 0
    below_par = sum(1 for r in items if r.get("par_level", 0) > 0) if items else 0

    k1, k2, k3 = st.columns(3)
    with k1:
        dash_kpi_card("Total Items", str(total_items), accent="navy")
    with k2:
        dash_kpi_card("Est. Value", "${:,.0f}".format(total_value), accent="green")
    with k3:
        dash_kpi_card("With Par Levels", str(below_par), accent="gold")

    # Add new item
    with st.expander("Add New Item"):
        c1, c2, c3 = st.columns(3)
        with c1:
            new_name = st.text_input("Item Name", key="inv_new_name")
            new_cat = st.selectbox("Category", _CATEGORIES, key="inv_new_cat")
        with c2:
            new_unit = st.selectbox("Unit", _UNITS, key="inv_new_unit")
            new_cost = st.number_input("Unit Cost ($)", min_value=0.0, step=0.01, key="inv_new_cost")
        with c3:
            new_par = st.number_input("Par Level", min_value=0.0, step=1.0, key="inv_new_par")
            new_supplier = st.text_input("Supplier", key="inv_new_supplier")
            new_dept = st.selectbox("Department", DEPARTMENTS, key="inv_new_dept")

        if st.button("Add Item", key="inv_add_btn"):
            if new_name.strip():
                try:
                    conn.execute(
                        """INSERT INTO inventory_items
                           (name, category, unit, unit_cost, par_level, supplier, department)
                           VALUES (?,?,?,?,?,?,?)""",
                        (new_name.strip(), new_cat, new_unit, new_cost,
                         new_par, new_supplier, new_dept),
                    )
                    conn.commit()
                    st.success("Added '{}'".format(new_name))
                    st.rerun()
                except Exception as e:
                    st.error("Item already exists or error: {}".format(e))
            else:
                st.warning("Enter an item name.")

    # Items table
    if items:
        df = pd.DataFrame([dict(r) for r in items])
        display_cols = ["name", "category", "unit", "unit_cost", "par_level", "supplier", "department"]
        display_cols = [c for c in display_cols if c in df.columns]
        df_display = df[display_cols].copy()
        df_display.columns = ["Name", "Category", "Unit", "Cost ($)", "Par Level", "Supplier", "Department"][:len(display_cols)]
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.caption("No items yet. Add your first item above.")


def _render_daily_count(conn, user):
    """Daily inventory count entry."""
    c1, c2 = st.columns(2)
    with c1:
        count_date = st.date_input("Count Date", date.today(), key="inv_count_date")
    with c2:
        count_dept = st.selectbox("Department", DEPARTMENTS, key="inv_count_dept")

    items = conn.execute(
        "SELECT * FROM inventory_items WHERE active=1 AND department=? ORDER BY category, name",
        (count_dept,)
    ).fetchall()

    if not items:
        st.caption("No items set up for {}. Add items in the Stock Items tab first.".format(count_dept))
        return

    # Load existing counts for this date
    existing = {}
    rows = conn.execute(
        "SELECT item_id, quantity FROM inventory_counts WHERE count_date=?",
        (count_date.isoformat(),)
    ).fetchall()
    for r in rows:
        existing[r["item_id"]] = r["quantity"]

    st.markdown("**Enter counts for {} items:**".format(len(items)))

    counts = {}
    current_cat = None
    for item in items:
        if item["category"] != current_cat:
            current_cat = item["category"]
            st.markdown("**{}**".format(current_cat))

        default_val = existing.get(item["id"], 0.0)
        val = st.number_input(
            "{} ({})".format(item["name"], item["unit"]),
            min_value=0.0, step=1.0,
            value=float(default_val),
            key="count_{}_{}".format(item["id"], count_date),
        )
        counts[item["id"]] = val

    if st.button("Save Counts", type="primary", key="inv_save_counts"):
        for item_id, qty in counts.items():
            conn.execute(
                """INSERT OR REPLACE INTO inventory_counts
                   (item_id, count_date, quantity, counted_by)
                   VALUES (?,?,?,?)""",
                (item_id, count_date.isoformat(), qty, user.get("username", "")),
            )
        conn.commit()
        st.success("Saved {} counts for {}".format(len(counts), count_date))


def _render_waste_log(conn, user):
    """Log food waste."""
    c1, c2 = st.columns(2)
    with c1:
        waste_date = st.date_input("Date", date.today(), key="waste_date")
    with c2:
        waste_dept = st.selectbox("Department", DEPARTMENTS, key="waste_dept")

    # Quick add form
    with st.expander("Log Waste", expanded=True):
        items = conn.execute(
            "SELECT id, name, unit, unit_cost FROM inventory_items WHERE active=1 AND department=? ORDER BY name",
            (waste_dept,)
        ).fetchall()

        if items:
            item_options = {"{} ({})".format(r["name"], r["unit"]): r for r in items}
            selected = st.selectbox("Item", list(item_options.keys()), key="waste_item")
            item = item_options[selected]
        else:
            st.text_input("Item Name", key="waste_item_name")
            item = None

        wc1, wc2 = st.columns(2)
        with wc1:
            waste_qty = st.number_input("Quantity Wasted", min_value=0.0, step=0.5, key="waste_qty")
        with wc2:
            waste_reason = st.selectbox("Reason", [
                "Expired", "Overproduction", "Spoiled", "Damaged",
                "Quality Issue", "Dropped", "Other",
            ], key="waste_reason")

        waste_cost = waste_qty * (item["unit_cost"] if item else 0)
        if waste_cost > 0:
            st.markdown("**Estimated cost: ${:,.2f}**".format(waste_cost))

        if st.button("Log Waste", key="waste_log_btn"):
            conn.execute(
                """INSERT INTO inventory_waste
                   (item_id, waste_date, quantity, reason, cost, department, logged_by)
                   VALUES (?,?,?,?,?,?,?)""",
                (item["id"] if item else None, waste_date.isoformat(),
                 waste_qty, waste_reason, waste_cost, waste_dept,
                 user.get("username", "")),
            )
            conn.commit()
            st.success("Logged {:.1f} {} waste — ${:,.2f}".format(
                waste_qty, selected if item else "", waste_cost))
            st.rerun()

    # Recent waste log
    recent = conn.execute(
        """SELECT w.*, i.name as item_name
           FROM inventory_waste w
           LEFT JOIN inventory_items i ON w.item_id = i.id
           WHERE w.department = ?
           ORDER BY w.waste_date DESC, w.created_at DESC
           LIMIT 20""",
        (waste_dept,)
    ).fetchall()

    if recent:
        dash_section_header("Recent Waste", "Last 20 entries")
        df = pd.DataFrame([dict(r) for r in recent])
        display = df[["waste_date", "item_name", "quantity", "reason", "cost", "logged_by"]].copy()
        display.columns = ["Date", "Item", "Qty", "Reason", "Cost ($)", "By"]
        st.dataframe(display, use_container_width=True, hide_index=True)

        # Summary
        total_waste = df["cost"].sum()
        st.markdown("**Total waste cost: ${:,.2f}**".format(total_waste))
    else:
        st.caption("No waste logged yet for {}.".format(waste_dept))


def _render_purchase_orders(conn, user):
    """Create and manage purchase orders."""
    c1, c2 = st.columns(2)
    with c1:
        po_dept = st.selectbox("Department", DEPARTMENTS, key="po_dept")
    with c2:
        po_status = st.selectbox("Status Filter", ["All", "draft", "submitted", "received"], key="po_status")

    # Fetch POs
    if po_status == "All":
        pos = conn.execute(
            "SELECT * FROM purchase_orders WHERE department=? ORDER BY order_date DESC LIMIT 20",
            (po_dept,)
        ).fetchall()
    else:
        pos = conn.execute(
            "SELECT * FROM purchase_orders WHERE department=? AND status=? ORDER BY order_date DESC LIMIT 20",
            (po_dept, po_status)
        ).fetchall()

    # Create new PO
    with st.expander("Create Purchase Order"):
        pc1, pc2 = st.columns(2)
        with pc1:
            po_supplier = st.text_input("Supplier", key="po_supplier")
            po_date = st.date_input("Order Date", date.today(), key="po_order_date")
        with pc2:
            po_delivery = st.date_input("Expected Delivery", date.today() + timedelta(days=3), key="po_delivery")
            po_notes = st.text_input("Notes", key="po_notes")

        # Items for PO
        st.markdown("**Order Items:**")
        items = conn.execute(
            "SELECT id, name, unit, unit_cost FROM inventory_items WHERE active=1 AND department=? ORDER BY name",
            (po_dept,)
        ).fetchall()

        po_line_items = []
        if items:
            for i, item in enumerate(items[:10]):  # Show first 10
                qty = st.number_input(
                    "{} ({} @ ${:.2f})".format(item["name"], item["unit"], item["unit_cost"]),
                    min_value=0.0, step=1.0,
                    key="po_qty_{}".format(item["id"]),
                )
                if qty > 0:
                    po_line_items.append({
                        "item_id": item["id"],
                        "name": item["name"],
                        "qty": qty,
                        "cost": item["unit_cost"],
                        "total": qty * item["unit_cost"],
                    })

        if po_line_items:
            po_total = sum(li["total"] for li in po_line_items)
            st.markdown("**Order Total: ${:,.2f}** ({} items)".format(po_total, len(po_line_items)))

        if st.button("Create PO", key="po_create_btn"):
            if po_supplier.strip() and po_line_items:
                po_total = sum(li["total"] for li in po_line_items)
                cursor = conn.execute(
                    """INSERT INTO purchase_orders
                       (supplier, order_date, delivery_date, department, status, total_cost, notes, created_by)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (po_supplier, po_date.isoformat(), po_delivery.isoformat(),
                     po_dept, "draft", po_total, po_notes, user.get("username", "")),
                )
                po_id = cursor.lastrowid
                for li in po_line_items:
                    conn.execute(
                        """INSERT INTO po_items (po_id, item_id, item_name, quantity, unit_cost, total_cost)
                           VALUES (?,?,?,?,?,?)""",
                        (po_id, li["item_id"], li["name"], li["qty"], li["cost"], li["total"]),
                    )
                conn.commit()
                st.success("PO #{} created — ${:,.2f}".format(po_id, po_total))
                st.rerun()
            else:
                st.warning("Add supplier and at least one item.")

    # PO list
    if pos:
        dash_section_header("Purchase Orders", "{} orders".format(len(pos)))
        for po in pos:
            status_color = {
                "draft": "#94A3B8", "submitted": "#3B82F6",
                "received": "#16A34A",
            }.get(po["status"], "#94A3B8")
            st.markdown(
                '<div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;'
                'padding:14px 18px;margin-bottom:8px;display:flex;justify-content:space-between;'
                'align-items:center;">'
                '<div>'
                '<span style="font-weight:600;color:#1E293B;">PO #{}</span>'
                ' — <span style="color:#64748B;">{}</span>'
                '<div style="font-size:12px;color:#94A3B8;margin-top:2px;">'
                '{} · {}</div></div>'
                '<div style="display:flex;align-items:center;gap:12px;">'
                '<span style="font-weight:600;color:#1E293B;">${:,.2f}</span>'
                '<span style="font-size:11px;font-weight:600;color:{};'
                'background:{}22;padding:3px 10px;border-radius:10px;'
                'text-transform:uppercase;">{}</span>'
                '</div></div>'.format(
                    po["id"], po["supplier"],
                    po["order_date"], po["department"],
                    po["total_cost"], status_color, status_color,
                    po["status"]),
                unsafe_allow_html=True,
            )
    else:
        st.caption("No purchase orders found.")
