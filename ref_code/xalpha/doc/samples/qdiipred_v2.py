# -*- coding: utf-8 -*-
"""
Enhanced QDII real-time net value prediction dashboard.
Features a premium light-themed design with purchase status column.
"""

import pandas as pd
import xalpha as xa
import logging
from datetime import datetime
from xalpha import investinghooks

# Configure logging
logger = logging.getLogger("xalpha")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(ch)

# Set backend - matching original qdiipred.py relative path
xa.set_backend(backend="csv", path="../../../lof/data", precached="20200103")

qdiis = [
    # General / Oil
    "SH501018",
    "SZ160416",
    "SZ161129",
    "SZ160723",
    "SZ162411",
    "SZ162719",
    "SZ161116",
    "SZ164701",
    "SZ160719",
    "SZ164824",
    "SH513050",
    "SZ159518",
    "SH513350",  # Oil & Gas
    # Nasdaq 100
    "SZ161130",
    "SH513100",
    "SZ159501",
    "SZ159941",
    "SZ159659",
    "SZ159513",
    "SZ159632",
    "SH513110",
    "SH513300",
    "SZ159696",
    "SH513870",
    "SH513390",
    "SZ159660",
    # S&P 500
    "SZ161125",
    "SH513500",
    "SZ159612",
    "SH513650",
    "SZ159655",  # "SZ165510" (No data source)
    # Other Indices
    "SZ159561",
    "SH513030",  # Germany
    "SH513400",  # Dow Jones
    "SH513080",  # France
    "SH520830",
    "SZ159329",  # Saudi
]
nonqdiis = [
    "SH501021",
    "SH513880",
    "SH513520",
    "SH513000",
    "SH510510",
    "SZ159922",
    "SH510500",
    "SH512500",
    "SZ159920",
]

data = {
    "Code": [],
    "Name": [],
    "Purchase Status": [],
    "T-1 Pred": [],
    "T-1 Rate (%)": [],
    "T-0 Pred": [],
    "T-0 Rate (%)": [],
    "Now": [],
    "Position": [],
}

print("Fetching QDII data...")
for c in qdiis:
    try:
        # 1. Fetch data into local variables
        p = xa.QDIIPredict(c, fetch=True, save=True, positions=True)
        f_info = xa.info.fundinfo(c[2:])
        status = f_info.purchase_status

        rt_info = xa.get_rt(c)
        name = rt_info["name"]
        now = rt_info["current"]

        t1_pred = round(p.get_t1(return_date=False), 4)
        t1_rate = round(p.get_t1_rate(return_date=False), 2)

        try:
            t0_pred = round(p.get_t0(return_date=False), 4)
            t0_rate = round(p.get_t0_rate(return_date=False), 2)
        except (ValueError, IndexError, KeyError):
            t0_pred = "-"
            t0_rate = "-"

        pos = round(p.get_position(return_date=False), 3)

        # 2. Atomic append to the main data structure
        data["Code"].append(c)
        data["Name"].append(name)
        data["Purchase Status"].append(status)
        data["T-1 Pred"].append(t1_pred)
        data["T-1 Rate (%)"].append(t1_rate)
        data["T-0 Pred"].append(t0_pred)
        data["T-0 Rate (%)"].append(t0_rate)
        data["Position"].append(pos)
        data["Now"].append(now)

    except Exception as e:
        print(f"Error processing QDII {c}: {e}")

print("Fetching Non-QDII data...")
for c in nonqdiis:
    try:
        # 1. Fetch data into local variables
        p = xa.RTPredict(c)
        f_info = xa.info.fundinfo(c[2:])
        status = f_info.purchase_status

        rt_info = xa.get_rt(c)
        name = rt_info["name"]
        now = rt_info["current"]

        # For non-QDII, T-1 Pred is just the current nav from info
        rt_f = xa.get_rt("F" + c[2:])
        t1_pred = rt_f["current"]

        try:
            t0_pred = round(p.get_t0(return_date=False), 4)
            t0_rate = round(p.get_t0_rate(return_date=False), 2)
        except (ValueError, IndexError, KeyError):
            t0_pred = "-"
            t0_rate = "-"

        # 2. Atomic append to the main data structure
        data["Code"].append(c)
        data["Name"].append(name)
        data["Purchase Status"].append(status)
        data["T-1 Pred"].append(t1_pred)
        data["T-1 Rate (%)"].append("-")
        data["T-0 Pred"].append(t0_pred)
        data["T-0 Rate (%)"].append(t0_rate)
        data["Position"].append("-")
        data["Now"].append(now)

    except Exception as e:
        print(f"Error processing Non-QDII {c}: {e}")

df = pd.DataFrame(data)

# Modern Light Theme HTML Template
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>xalpha QDII Prediction Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
    <style>
        :root {{
            --bg-color: #f8fafc;
            --card-bg: rgba(255, 255, 255, 0.8);
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --accent-color: #3b82f6;
            --positive: #10b981;
            --negative: #ef4444;
            --warning: #f59e0b;
            --border-color: #e2e8f0;
        }}

        body {{
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            margin: 0;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}

        .header {{
            text-align: center;
            margin-bottom: 2rem;
            width: 100%;
            max-width: 1200px;
        }}

        .header h1 {{
            font-size: 2.5rem;
            font-weight: 600;
            margin: 0;
            background: linear-gradient(135deg, #1e293b 0%, #3b82f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .header p {{
            color: var(--text-secondary);
            margin-top: 0.5rem;
        }}

        .container {{
            width: 100%;
            max-width: 1200px;
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            border: 1px solid var(--border-color);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th {{
            background-color: #f1f5f9;
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
            padding: 1rem;
            border-bottom: 2px solid var(--border-color);
        }}

        td {{
            padding: 1rem;
            border-bottom: 1px solid var(--border-color);
            font-size: 0.875rem;
            text-align: center;
        }}

        tr:hover {{
            background-color: #f8fafc;
        }}

        .status-tag {{
            padding: 0.25rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .status-open {{ background-color: #dcfce7; color: #166534; }}
        .status-closed {{ background-color: #fee2e2; color: #991b1b; }}
        .status-warning {{ background-color: #fef3c7; color: #92400e; }}
        .status-unknown {{ background-color: #f1f5f9; color: #475569; }}

        .rate-pos {{ color: var(--positive); font-weight: 600; }}
        .rate-neg {{ color: var(--negative); font-weight: 600; }}

        .footer {{
            margin-top: 2rem;
            color: var(--text-secondary);
            font-size: 0.875rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>QDII Prediction Dashboard</h1>
        <p>Generated at: {timestamp}</p>
    </div>

    <div class="container">
        <table id="predictionTable" class="display">
            <thead>
                <tr>
                    <th>Code</th>
                    <th>Name</th>
                    <th>Status</th>
                    <th>T-1 Pred</th>
                    <th>T-1 %</th>
                    <th>T-0 Pred</th>
                    <th>T-0 %</th>
                    <th>Now</th>
                    <th>Position</th>
                </tr>
            </thead>
            <tbody>
"""

footer = """
            </tbody>
        </table>
    </div>

    <div class="footer">
        Powered by xalpha framework &bull; Designed by Antigravity
    </div>

    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <script>
        $(document).ready(function() {
            $('#predictionTable').DataTable({
                paging: false,
                info: false,
                searching: true,
                order: [[4, 'desc']], // Order by T-1 % by default
                columnDefs: [
                    { targets: [4, 6], render: function(data, type, row) {
                        if (type === 'display') {
                            if (data === '-') return data;
                            var val = parseFloat(data);
                            var colorClass = val >= 0 ? 'rate-pos' : 'rate-neg';
                            var prefix = val >= 0 ? '+' : '';
                            return '<span class="' + colorClass + '">' + prefix + data + '%</span>';
                        }
                        return data;
                    }},
                    { targets: 2, render: function(data, type, row) {
                        if (type === 'display') {
                            var cssClass = 'status-unknown';
                            if (data.includes('开放')) cssClass = 'status-open';
                            else if (data.includes('暂停')) cssClass = 'status-closed';
                            else if (data.includes('限额')) cssClass = 'status-warning';
                            return '<span class="status-tag ' + cssClass + '">' + data + '</span>';
                        }
                        return data;
                    }}
                ]
            });
        });
    </script>
</body>
</html>
"""

# Build table rows
rows = ""
for index, row in df.iterrows():
    rows += f"""
                <tr>
                    <td>{row['Code']}</td>
                    <td>{row['Name']}</td>
                    <td>{row['Purchase Status']}</td>
                    <td>{row['T-1 Pred']}</td>
                    <td>{row['T-1 Rate (%)']}</td>
                    <td>{row['T-0 Pred']}</td>
                    <td>{row['T-0 Rate (%)']}</td>
                    <td>{row['Now']}</td>
                    <td>{row['Position']}</td>
                </tr>
    """

full_html = html_template + rows + footer

with open("qdii_enhanced.html", "w", encoding="utf-8") as f:
    f.write(full_html)

print("Enhanced dashboard generated successfully: qdii_enhanced.html")
