你是一位资深全栈工程师，对以下技术栈有深入的理解和丰富的实战经验：
后端: Python, FastAPI, Playwright
前端: Vue.js 3, Vite, Pinia, Element Plus
你的任务是为一个已有的、遵循这些技术栈标准实践的项目，设计并实现一个“可视化元素选择器”功能。你的实现必须是模块化的，并且能够无缝集成到遵循标准设计模式的项目中。
核心任务 (Core Task)
创建一个完整的可视化元素选择功能。该功能将允许用户在一个新页面上加载任何目标网站，通过点击页面元素，自动生成用于监控的 CSS Selector 和 XPath，并最终将这些规则用于创建监控任务。
详细实现计划 (Detailed Implementation Plan)
请按照以下三个独立模块的描述来构建你的解决方案。
模块一：后端 API (Python/FastAPI)
创建代理渲染端点 (Proxy Rendering Endpoint):
在你的 FastAPI 应用中，设立一个新的 API 路由器（Router）。
在该路由器上，定义一个 POST 路径操作（Path Operation），用于接收客户端发送的目标 URL。
此端点的核心逻辑应使用 Playwright，并以异步方式执行以下步骤：
接收请求体中的 url。
启动浏览器，打开新页面，并导航到该 url。
务必等待页面上的动态内容（JavaScript）执行完毕并达到网络空闲状态（networkidle）。
读取一个独立的、将在下一步中创建的 injector.js 脚本文件的内容。
获取 Playwright 渲染后的完整页面 HTML。
将 injector.js 的脚本内容注入到该 HTML 的 <body> 标签闭合之前。
将注入脚本后的完整 HTML 字符串，通过 FastAPI 的 HTMLResponse 类返回给前端。
提供注入脚本 (Serve the Injector Script):
创建一个名为 injector.js 的纯 JavaScript 文件。
配置你的 FastAPI 应用，使其能够通过一个静态文件路径（例如 /static/injector.js）来提供这个脚本。
模块二：前端视图 (Vue.js/Element Plus)
创建功能主页面组件:
创建一个新的、符合路由标准的主视图组件（View Component）。
在你的 Vue Router 配置中，为这个新组件添加一条路由规则，使其可以通过一个独立的 URL 访问。
实现页面布局与交互:
使用 Element Plus 的布局组件（如 Container, Header, Aside, Main）来构建用户界面。
界面应包括：一个用于输入 URL 的输入框、一个“加载”按钮、一个用于展示目标网站的 <iframe>，以及一个用于显示结果的侧边栏。
使用 Vue 3 的组合式 API (<script setup>) 来管理组件的状态和逻辑。
实现核心功能逻辑:
状态管理: 使用 ref 或 reactive 来管理 isLoading, iframeSrcDoc, selectionResult 等响应式状态。
数据获取: 当用户点击“加载”按钮时，向你在模块一中创建的后端代理端点发送一个 POST 请求。在请求期间，显示加载动画（如 Element Plus 的 v-loading）。
渲染 Iframe: 将后端成功返回的、包含注入脚本的 HTML 字符串，赋值给一个状态变量，并使用 :srcdoc 属性将其绑定到 <iframe> 上。
跨窗口通信: 在组件的 onMounted 生命周期钩子中，注册一个全局 message 事件监听器 (window.addEventListener)。此监听器专门用于接收来自 <iframe> 中 injector.js 脚本通过 postMessage 发送的数据。在 onUnmounted 钩子中务必移除此监听器以防内存泄漏。
结果展示: 当接收到选择结果数据后，更新 selectionResult 状态，并在侧边栏使用 Element Plus 的描述组件（Descriptions）进行格式化展示。
模块三：网页注入脚本 (injector.js)
此脚本必须是框架无关的纯 JavaScript，以便在任何网页环境中运行。
元素交互:
监听 mouseover 和 mouseout 事件，实现一个动态的、跟手的高亮效果（例如，蓝色边框）。
监听 click 事件。当用户点击时，取消高亮效果，将该元素标记为“已选中”（例如，红色边框），并阻止事件的进一步传播。
在选中的元素附近，动态创建一个浮动面板（Popover），面板上提供“确认”和“重新选择”两个按钮。
规则生成算法:
CSS Selector 生成: 编写一个函数，当用户点击“确认”时，从被选中的元素开始，向上遍历 DOM 树，生成一个尽可能简短且唯一的 CSS 选择器。算法应优先使用元素的 id，其次是 tagName、class 和 :nth-child 的组合。
XPath 生成: 编写一个函数，生成从根节点到选中元素的完整、索引化的 XPath 路径。
模式推断:
分析选中元素在其父元素中的同类型兄弟节点的数量和位置，推断出该元素是属于“固定区域”还是“列表中的最新一条”。
与父通信:
当用户点击“确认”后，将所有生成的数据（CSS Selector, XPath, 推荐模式, 元素的 innerText 等）打包成一个 JSON 对象。
使用 window.parent.postMessage(yourResultObject, '*') 将这个对象发送到外层的 Vue 应用。
交付要求
请为上述三个模块提供完整、高质量、遵循最佳实践的代码。代码应包含清晰的注释，特别是在算法实现、异步操作和跨窗口通信等关键逻辑部分。