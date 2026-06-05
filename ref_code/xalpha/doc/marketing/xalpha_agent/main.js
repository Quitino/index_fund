const chatFlow = document.getElementById('chat-flow');

const messages = [
    {
        type: 'user',
        label: 'Investor',
        text: '帮我分析一下 500 增强基金里，哪些在 2023 年这种震荡市表现最好？回撤要控制在 15% 以内。'
    },
    {
        type: 'agent',
        label: 'xalpha Agent',
        text: '好的，正在扫描全市场中证 500 指数增强型基金... 我将通过 xalpha 获取 2023 年全年的回测数据，并按卡玛比率进行排序。'
    },
    {
        type: 'agent',
        label: 'Executing System',
        isCode: true,
        text: `import xalpha as xa
df = xa.universal.get_enhanced_funds("CSI500")
results = []
for code in df['code']:
    bt = xa.trade.backtest(code, start="20230101", end="20231231")
    if bt.max_drawdown < 0.15:
        results.append(bt.summary())`
    },
    {
        type: 'agent',
        label: 'xalpha Agent',
        text: '分析完成！表现最优的前三名分别是：景顺长城 500 增强 (000311)... 它们的平均超额收益达到了 8.2%，且回撤均成功控制在 12% 左右。需要我生成完整的 HTML 分析报告吗？'
    }
];

function createMessage(msg) {
    const div = document.createElement('div');
    div.className = `message ${msg.type}`;
    
    let content = `
        <span class="label">${msg.label}</span>
        <div class="bubble">
            ${msg.isCode ? `<pre class="code-block">${msg.text}</pre>` : msg.text}
        </div>
    `;
    
    div.innerHTML = content;
    return div;
}

async function startChat() {
    for (const msg of messages) {
        const msgEl = createMessage(msg);
        chatFlow.appendChild(msgEl);
        
        // Small delay for natural feel
        await new Promise(resolve => setTimeout(resolve, 500));
        msgEl.classList.add('visible');
        
        // Wait longer before next message
        await new Promise(resolve => setTimeout(resolve, msg.isCode ? 3000 : 2000));
    }
}

// Start animation when scrolled into view
const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
        startChat();
        observer.disconnect();
    }
}, { threshold: 0.5 });

observer.observe(document.getElementById('demo'));
