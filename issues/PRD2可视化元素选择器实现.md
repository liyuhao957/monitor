# PRD2可视化元素选择器实现任务

## 任务背景
用户当前需要手动选取CSS Selector、XPath、Regex、Full Text，希望实现PRD2中描述的可视化元素选择器功能，自动化这个过程。

## 实现方案
采用完整的三模块实现方案：
1. 后端API (Python/FastAPI)
2. 前端视图 (Vue.js/Element Plus)  
3. 注入脚本 (纯JavaScript)

## 详细实现计划

### 文件修改清单
1. **创建 `backend/app/api/selector.py`** - 新的API路由器
2. **创建 `backend/static/injector.js`** - 元素选择脚本
3. **修改 `backend/app/main.py`** - 注册路由和静态文件
4. **创建 `frontend/src/views/SelectorView.vue`** - 主视图组件
5. **修改 `frontend/src/router/index.ts`** - 添加路由
6. **修改 `frontend/src/App.vue`** - 更新导航
7. **修改 `frontend/src/services/api.ts`** - API服务

### 实施步骤
1. 后端API实现 - selector路由器和Playwright集成
2. 注入脚本开发 - 元素选择和算法实现
3. 前端视图开发 - Vue组件和交互逻辑
4. 路由和导航集成 - 完整用户流程
5. 测试和优化 - 功能验证和错误处理

### 预期结果
- 用户通过/selector访问元素选择器
- 安全加载任意URL到iframe
- 点击元素自动生成CSS Selector和XPath
- 生成的选择器可用于创建监控任务

## 执行状态
- [x] 计划制定完成
- [x] 后端API实现
- [x] 注入脚本开发
- [x] 前端视图开发
- [x] 路由和导航集成
- [x] 基础功能测试

## 实现完成情况
✅ **后端API** - 创建了完整的selector.py路由器，包含：
- POST /api/selector/load - 创建选择器会话
- GET /api/selector/render/{session_id} - 渲染页面并注入脚本
- DELETE /api/selector/session/{session_id} - 清理会话

✅ **注入脚本** - 创建了功能完整的injector.js，包含：
- 元素高亮交互（鼠标悬停/离开）
- 点击选择和确认逻辑
- CSS Selector和XPath生成算法
- 模式推断（固定区域/列表项/最新内容）
- 跨窗口通信（postMessage）

✅ **前端视图** - 创建了SelectorView.vue组件，包含：
- URL输入和验证
- iframe安全加载目标网站
- 实时消息监听和结果展示
- 错误处理和用户引导

✅ **集成完成** - 系统集成包含：
- 添加了/selector路由配置
- 更新了导航菜单
- 后端服务正常启动
- 前端页面可正常访问

## 功能验证
- 后端服务启动成功 ✅
- 前端页面加载正常 ✅
- 路由导航工作正常 ✅
- 准备进行完整功能测试 🔄
