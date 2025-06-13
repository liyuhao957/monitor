/**
 * 可视化元素选择器注入脚本
 * 提供元素高亮、选择和规则生成功能
 */

(function() {
    'use strict';
    
    // 全局状态
    let isActive = true;
    let selectedElement = null;
    let highlightedElement = null;
    let popover = null;
    
    // 样式常量
    const HIGHLIGHT_STYLE = {
        outline: '2px solid #007bff',
        outlineOffset: '1px',
        cursor: 'pointer'
    };
    
    const SELECTED_STYLE = {
        outline: '2px solid #dc3545',
        outlineOffset: '1px',
        backgroundColor: 'rgba(220, 53, 69, 0.1)'
    };
    
    // 初始化
    function init() {
        console.log('Element Selector Injector initialized');
        console.log('Document ready state:', document.readyState);
        console.log('Window location:', window.location.href);
        addEventListeners();
        addStyles();
    }
    
    // 添加样式
    function addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .selector-popover {
                position: absolute;
                background: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 15px;
                z-index: 10000;
                font-family: Arial, sans-serif;
                font-size: 12px;
                min-width: 400px;
                max-width: 600px;
                max-height: 500px;
                overflow-y: auto;
            }
            .selector-popover button {
                margin: 0 5px;
                padding: 5px 10px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background: white;
                cursor: pointer;
            }
            .selector-popover button:hover {
                background: #f0f0f0;
            }
            .selector-popover button.primary {
                background: #007bff;
                color: white;
                border-color: #007bff;
            }
            .selector-popover button.primary:hover {
                background: #0056b3;
            }
            .selector-popover .target-option {
                background: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 3px;
                padding: 8px 10px;
                margin: 4px 0;
                font-family: monospace;
                font-size: 11px;
                line-height: 1.4;
                word-break: break-all;
                white-space: pre-wrap;
            }
            .selector-popover .target-option:hover {
                background: #e9ecef;
            }
        `;
        document.head.appendChild(style);
    }
    
    // 添加事件监听器
    function addEventListeners() {
        document.addEventListener('mouseover', handleMouseOver, true);
        document.addEventListener('mouseout', handleMouseOut, true);
        document.addEventListener('click', handleClick, true);
        document.addEventListener('keydown', handleKeyDown, true);
    }
    
    // 鼠标悬停处理
    function handleMouseOver(event) {
        if (!isActive || selectedElement) return;
        
        const element = event.target;
        if (element === highlightedElement) return;
        
        clearHighlight();
        highlightElement(element);
    }
    
    // 鼠标离开处理
    function handleMouseOut(event) {
        if (!isActive || selectedElement) return;
        // 延迟清除高亮，避免快速移动时闪烁
        setTimeout(() => {
            if (event.target === highlightedElement) {
                clearHighlight();
            }
        }, 50);
    }
    
    // 点击处理
    function handleClick(event) {
        console.log('Click event triggered, isActive:', isActive);
        if (!isActive) return;

        const element = event.target;
        console.log('Clicked element:', element);

        // 如果点击的是弹窗内的元素
        const popoverElement = element.closest('.selector-popover');
        if (popoverElement) {
            console.log('Click on popover element:', element);
            // 如果是确认或重选按钮，不要阻止事件，让它正常传播
            if (element.classList.contains('confirm-btn') || element.classList.contains('reselect-btn')) {
                console.log('Click on popover button, not preventing default');
                // 不要preventDefault和stopPropagation，让按钮的事件监听器正常工作
                return;
            }
            // 如果是单选按钮、标签或标签内的文本元素，允许正常交互
            if (element.type === 'radio' ||
                element.tagName.toLowerCase() === 'label' ||
                element.closest('label') ||
                ['strong', 'span', 'br'].includes(element.tagName.toLowerCase())) {
                console.log('Click on radio button, label, or label content, allowing default behavior');
                // 不阻止默认行为，但阻止事件冒泡
                event.stopPropagation();
                return;
            }
            console.log('Click on other popover area, ignoring');
            event.preventDefault();
            event.stopPropagation();
            return;
        }

        event.preventDefault();
        event.stopPropagation();
        selectElement(element);
    }
    
    // 键盘处理
    function handleKeyDown(event) {
        if (event.key === 'Escape') {
            if (selectedElement) {
                deselectElement();
            } else {
                deactivate();
            }
        }
    }
    
    // 高亮元素
    function highlightElement(element) {
        highlightedElement = element;
        const originalStyle = element.style.cssText;
        element.dataset.originalStyle = originalStyle;
        
        Object.assign(element.style, HIGHLIGHT_STYLE);
    }
    
    // 清除高亮
    function clearHighlight() {
        if (highlightedElement) {
            const originalStyle = highlightedElement.dataset.originalStyle || '';
            highlightedElement.style.cssText = originalStyle;
            delete highlightedElement.dataset.originalStyle;
            highlightedElement = null;
        }
    }
    
    // 选择元素
    function selectElement(element) {
        console.log('selectElement called with:', element);

        // 清除之前的选择
        if (selectedElement) {
            deselectElement();
        }

        clearHighlight();
        selectedElement = element;

        // 应用选中样式
        const originalStyle = element.style.cssText;
        element.dataset.selectedOriginalStyle = originalStyle;
        Object.assign(element.style, SELECTED_STYLE);

        console.log('About to show popover for element:', element);

        // 显示弹窗
        showPopover(element);

        console.log('showPopover completed');
    }
    
    // 取消选择元素
    function deselectElement() {
        if (selectedElement) {
            const originalStyle = selectedElement.dataset.selectedOriginalStyle || '';
            selectedElement.style.cssText = originalStyle;
            delete selectedElement.dataset.selectedOriginalStyle;
            selectedElement = null;
        }
        
        hidePopover();
    }
    
    // 显示弹窗
    function showPopover(element) {
        hidePopover();

        // 获取可选的父容器
        const parentOptions = getParentContainerOptions(element);

        popover = document.createElement('div');
        popover.className = 'selector-popover';

        let parentOptionsHtml = '';
        if (parentOptions.length > 1) {
            parentOptionsHtml = `
                <div style="margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px;">
                    <div style="font-weight: bold; margin-bottom: 8px;">选择目标元素:</div>
                    ${parentOptions.map((option, index) => {
                        const escapedDescription = option.description.replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                        return `
                        <div style="margin: 6px 0; padding: 6px; border: 1px solid #e0e0e0; border-radius: 4px; background: ${index === 0 ? '#f0f8ff' : '#f9f9f9'};">
                            <label style="display: block; cursor: pointer; font-size: 12px;">
                                <input type="radio" name="target-element" value="${index}" ${index === 0 ? 'checked' : ''} style="margin-right: 8px;">
                                <strong>${index === 0 ? '当前元素' : `父容器 ${index}`}</strong>
                                <br>
                                <span style="color: #666; font-size: 10px; font-family: monospace; word-break: break-all;">
                                    ${escapedDescription}
                                </span>
                            </label>
                        </div>
                        `;
                    }).join('')}
                </div>
            `;
        }

        popover.innerHTML = `
            ${parentOptionsHtml}
            <div style="font-weight: bold; margin-bottom: 10px;">监控类型:</div>
            <div style="margin: 5px 0;">
                <label style="display: block; margin: 5px 0; cursor: pointer;">
                    <input type="radio" name="monitor-intent" value="fixed" style="margin-right: 5px;">
                    监控这个固定位置的内容
                </label>
                <div style="font-size: 11px; color: #666; margin-left: 20px; margin-bottom: 8px;">
                    只监控当前选中的这个具体元素
                </div>

                <label style="display: block; margin: 5px 0; cursor: pointer;">
                    <input type="radio" name="monitor-intent" value="latest" style="margin-right: 5px;" checked>
                    监控列表中的最新一条
                </label>
                <div style="font-size: 11px; color: #666; margin-left: 20px; margin-bottom: 8px;">
                    总是获取列表第一个位置的内容，无论内容如何更新
                </div>

                <label style="display: block; margin: 5px 0; cursor: pointer;">
                    <input type="radio" name="monitor-intent" value="list" style="margin-right: 5px;">
                    监控整个列表的变化
                </label>
                <div style="font-size: 11px; color: #666; margin-left: 20px; margin-bottom: 10px;">
                    监控列表中所有项目的变化
                </div>
            </div>
            <div style="margin: 10px 0; text-align: center;">
                <button class="primary confirm-btn">确认选择</button>
                <button class="reselect-btn">重新选择</button>
            </div>
        `;

        // 定位弹窗
        const rect = element.getBoundingClientRect();
        popover.style.left = (rect.left + window.scrollX) + 'px';
        popover.style.top = (rect.bottom + window.scrollY + 5) + 'px';

        document.body.appendChild(popover);

        // 添加按钮事件监听器
        const confirmBtn = popover.querySelector('.confirm-btn');
        const reselectBtn = popover.querySelector('.reselect-btn');

        console.log('Popover HTML:', popover.innerHTML);
        console.log('Found confirm button:', confirmBtn);
        console.log('Found reselect button:', reselectBtn);

        if (confirmBtn) {
            console.log('Adding click listener to confirm button');
            confirmBtn.addEventListener('click', function(e) {
                console.log('Confirm button clicked!');
                e.preventDefault();
                e.stopPropagation();
                confirmSelection();
            });
        } else {
            console.error('Confirm button not found!');
        }

        if (reselectBtn) {
            console.log('Adding click listener to reselect button');
            reselectBtn.addEventListener('click', function(e) {
                console.log('Reselect button clicked!');
                e.preventDefault();
                e.stopPropagation();
                reselectElement();
            });
        } else {
            console.error('Reselect button not found!');
        }

        // 为单选按钮添加change事件监听器，确保选中状态正确更新
        const radioButtons = popover.querySelectorAll('input[type="radio"]');
        radioButtons.forEach(radio => {
            radio.addEventListener('change', function(e) {
                console.log('Radio button changed:', e.target.name, '=', e.target.value);
                // 更新视觉反馈
                if (e.target.name === 'target-element') {
                    updateTargetElementSelection(e.target.value);
                } else if (e.target.name === 'monitor-intent') {
                    updateMonitorIntentSelection(e.target.value);
                }
            });
        });
    }

    // 更新目标元素选择的视觉反馈
    function updateTargetElementSelection(selectedIndex) {
        console.log('Updating target element selection to index:', selectedIndex);

        // 更新所有选项的背景色
        const targetOptions = popover.querySelectorAll('div[style*="margin: 6px 0"]');
        targetOptions.forEach((option, index) => {
            if (index.toString() === selectedIndex) {
                // 选中的选项用蓝色背景
                option.style.background = '#f0f8ff';
                option.style.borderColor = '#007bff';
            } else {
                // 未选中的选项用灰色背景
                option.style.background = '#f9f9f9';
                option.style.borderColor = '#e0e0e0';
            }
        });
    }

    // 更新监控类型选择的视觉反馈
    function updateMonitorIntentSelection(selectedValue) {
        console.log('Updating monitor intent selection to:', selectedValue);

        // 找到所有监控类型的label
        const intentLabels = popover.querySelectorAll('input[name="monitor-intent"]');
        intentLabels.forEach(radio => {
            const label = radio.closest('label');
            if (label) {
                if (radio.value === selectedValue) {
                    // 选中的选项加粗并添加背景色
                    label.style.fontWeight = 'bold';
                    label.style.backgroundColor = '#f0f8ff';
                    label.style.padding = '8px';
                    label.style.borderRadius = '4px';
                    label.style.border = '1px solid #007bff';
                } else {
                    // 未选中的选项恢复正常样式
                    label.style.fontWeight = 'normal';
                    label.style.backgroundColor = 'transparent';
                    label.style.padding = '0';
                    label.style.borderRadius = '0';
                    label.style.border = 'none';
                }
            }
        });
    }

    // 获取父容器选项
    function getParentContainerOptions(element) {
        const options = [];
        let current = element;
        let depth = 0;
        const maxDepth = 5; // 最多向上查找5层

        while (current && depth < maxDepth) {
            const tagName = current.tagName.toLowerCase();

            // 获取更好的文本预览
            let textPreview = '';
            if (current.textContent) {
                const text = current.textContent.trim();
                if (text.length > 100) {
                    textPreview = text.substring(0, 100) + '...';
                } else {
                    textPreview = text;
                }
                // 替换换行符和多余空格
                textPreview = textPreview.replace(/\s+/g, ' ');
            }

            const className = current.className ? ` class="${current.className.split(' ')[0]}"` : '';
            const id = current.id ? ` id="${current.id}"` : '';

            // 创建更清晰的描述
            let description = `<${tagName}${id}${className}>`;
            if (textPreview) {
                description += ` "${textPreview}"`;
            }

            options.push({
                element: current,
                description: description,
                isTableRow: tagName === 'tr',
                isListItem: tagName === 'li',
                isContainer: ['div', 'section', 'article'].includes(tagName) && current.children.length > 1
            });

            current = current.parentElement;
            depth++;

            // 如果到达body或html，停止
            if (!current || tagName === 'body' || tagName === 'html') {
                break;
            }
        }

        return options;
    }

    // 隐藏弹窗
    function hidePopover() {
        if (popover) {
            popover.remove();
            popover = null;
        }

        // 弹窗已移除，事件监听器会自动清理
    }
    
    // 确认选择
    async function confirmSelection() {
        console.log('confirmSelection called, selectedElement:', selectedElement);
        if (!selectedElement) {
            console.error('No element selected');
            return;
        }

        // 获取用户选择的监控意图
        const selectedIntent = popover.querySelector('input[name="monitor-intent"]:checked');
        if (!selectedIntent) {
            alert('请选择监控类型');
            return;
        }

        // 获取用户选择的目标元素
        let targetElement = selectedElement;
        const selectedTarget = popover.querySelector('input[name="target-element"]:checked');
        if (selectedTarget) {
            const parentOptions = getParentContainerOptions(selectedElement);
            const targetIndex = parseInt(selectedTarget.value);
            if (parentOptions[targetIndex]) {
                targetElement = parentOptions[targetIndex].element;
                console.log('User selected parent element:', targetElement);
            }
        }

        const intent = selectedIntent.value;
        console.log('User selected intent:', intent);
        console.log('Target element:', targetElement);

        // 显示加载状态
        showLoadingState();

        try {
            // 使用AI生成选择器
            const result = await generateAISelector(targetElement, intent);
            console.log('AI Generated selectors:', result);
            sendResultToParent(result);
        } catch (error) {
            console.error('AI选择器生成失败:', error);
            alert('选择器生成失败，请重试');
        } finally {
            hideLoadingState();
        }

        // 只清理当前选择状态，不停用整个选择器
        deselectElement();
        // 不调用 deactivate()，让用户可以继续选择其他元素
    }
    
    // 重新选择
    function reselectElement() {
        console.log('Reselect button clicked');
        deselectElement();
        // 选择器保持激活状态，用户可以继续选择
    }

    // 使用AI生成选择器
    async function generateAISelector(element, intent) {
        // 收集元素信息
        const elementData = collectElementData(element, intent);

        // 调用AI API
        const requestData = {
            element_html: elementData.elementHtml,
            context_html: elementData.contextHtml,
            user_intent: intent,
            element_text: elementData.elementText,
            element_attributes: elementData.elementAttributes
        };

        console.log('发送给AI的数据:', requestData);

        // 确保使用正确的API地址
        const apiUrl = window.location.origin.includes('localhost:8000')
            ? 'http://localhost:8000/api/selector/ai-generate'
            : '/api/selector/ai-generate';

        console.log('API URL:', apiUrl);

        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'AI API调用失败');
        }

        return await response.json();
    }

    // 收集元素数据
    function collectElementData(element, intent = 'fixed') {
        // 获取精确的路径信息
        const pathInfo = collectPrecisePathInfo(element);

        // 根据意图获取合适的示例文本
        const elementText = getExampleTextByIntent(element, intent);

        // 获取元素属性（过滤掉临时属性）
        const elementAttributes = {};
        const tempAttributes = ['data-selected-original-style', 'style'];
        for (let attr of element.attributes) {
            // 跳过临时属性和包含特定关键词的属性
            if (!tempAttributes.includes(attr.name) &&
                !attr.name.includes('selected') &&
                !attr.name.includes('highlight') &&
                !attr.name.includes('outline')) {
                elementAttributes[attr.name] = attr.value;
            }
        }

        return {
            elementHtml: pathInfo.elementHtml,
            elementText,
            elementAttributes,
            contextHtml: pathInfo.pathDescription,
            elementPath: pathInfo.uniquePath,
            cssPath: pathInfo.cssPath,
            xpathPath: pathInfo.xpathPath
        };
    }

    // 根据意图获取合适的示例文本
    function getExampleTextByIntent(element, intent) {
        switch (intent) {
            case 'latest':
                // 对于latest意图，获取列表中第一个项目的文本
                if (element.tagName.toLowerCase() === 'ul' || element.tagName.toLowerCase() === 'ol') {
                    const firstItem = element.querySelector('li');
                    if (firstItem) {
                        return firstItem.textContent ? firstItem.textContent.trim() : '';
                    }
                }
                // 如果不是列表，或者没有找到第一个项目，返回元素自身的直接文本
                return getDirectTextContent(element);

            case 'fixed':
                // 对于fixed意图，返回元素的直接文本内容
                return getDirectTextContent(element);

            default:
                // 默认返回元素的所有文本内容
                return element.textContent ? element.textContent.trim() : '';
        }
    }

    // 获取元素的直接文本内容（不包括子元素）
    function getDirectTextContent(element) {
        let text = '';
        for (let node of element.childNodes) {
            if (node.nodeType === Node.TEXT_NODE) {
                text += node.textContent;
            }
        }
        return text.trim();
    }

    // 收集精确路径信息
    function collectPrecisePathInfo(targetElement) {
        // 创建目标元素的干净副本
        const cleanElement = targetElement.cloneNode(true);
        cleanElementAttributes(cleanElement);

        // 计算从根到目标元素的完整路径
        const pathChain = buildCompletePathChain(targetElement);

        // 生成唯一的CSS和XPath路径
        const uniquePaths = generateUniquePaths(pathChain);

        // 创建路径描述
        const pathDescription = createPathDescription(pathChain);

        return {
            elementHtml: cleanElement.outerHTML,
            pathDescription: pathDescription,
            uniquePath: pathChain,
            cssPath: uniquePaths.css,
            xpathPath: uniquePaths.xpath
        };
    }

    // 构建完整路径链
    function buildCompletePathChain(element) {
        const pathChain = [];
        let current = element;

        while (current && current !== document.documentElement) {
            const nodeInfo = {
                tagName: current.tagName.toLowerCase(),
                attributes: {},
                position: 0,
                totalSiblings: 0,
                uniqueIdentifiers: []
            };

            // 收集属性（过滤临时属性）
            const tempAttributes = ['data-selected-original-style', 'style'];
            for (let attr of current.attributes) {
                if (!tempAttributes.includes(attr.name) &&
                    !attr.name.includes('selected') &&
                    !attr.name.includes('highlight') &&
                    !attr.name.includes('outline')) {
                    nodeInfo.attributes[attr.name] = attr.value;
                }
            }

            // 计算位置信息
            if (current.parentElement) {
                const siblings = Array.from(current.parentElement.children);
                const sameTags = siblings.filter(sibling => sibling.tagName === current.tagName);
                nodeInfo.position = sameTags.indexOf(current) + 1;
                nodeInfo.totalSiblings = sameTags.length;
            }

            // 识别唯一标识符
            if (nodeInfo.attributes.id) {
                nodeInfo.uniqueIdentifiers.push(`id="${nodeInfo.attributes.id}"`);
            }

            if (nodeInfo.attributes.class) {
                const classes = nodeInfo.attributes.class.trim().split(/\s+/)
                    .filter(c => c && !c.includes('selected') && !c.includes('highlight'));
                if (classes.length > 0) {
                    nodeInfo.uniqueIdentifiers.push(`class="${classes.join(' ')}"`);
                }
            }

            // 检查其他有意义的属性
            ['data-id', 'data-testid', 'role', 'name'].forEach(attr => {
                if (nodeInfo.attributes[attr]) {
                    nodeInfo.uniqueIdentifiers.push(`${attr}="${nodeInfo.attributes[attr]}"`);
                }
            });

            pathChain.unshift(nodeInfo);
            current = current.parentElement;
        }

        return pathChain;
    }

    // 生成唯一路径
    function generateUniquePaths(pathChain) {
        const cssPath = [];
        const xpathPath = [];

        for (let i = 0; i < pathChain.length; i++) {
            const node = pathChain[i];
            let cssSelector = node.tagName;
            let xpathSelector = node.tagName;

            // 优先使用ID
            if (node.attributes.id) {
                cssSelector = `${node.tagName}#${node.attributes.id}`;
                xpathSelector = `${node.tagName}[@id="${node.attributes.id}"]`;
                cssPath.push(cssSelector);
                xpathPath.push(xpathSelector);
                break; // 有ID就足够唯一了
            }

            // 使用稳定的类名
            if (node.attributes.class) {
                const classes = node.attributes.class.trim().split(/\s+/)
                    .filter(c => c && !c.includes('selected') && !c.includes('highlight'));
                if (classes.length > 0) {
                    const stableClass = classes.find(c =>
                        c.includes('content') || c.includes('main') || c.includes('container')
                    ) || classes[0];
                    cssSelector += `.${stableClass}`;
                    xpathSelector += `[@class="${node.attributes.class}"]`;
                }
            }

            // 如果有其他唯一属性
            if (node.attributes['data-id']) {
                xpathSelector += `[@data-id="${node.attributes['data-id']}"]`;
            }

            // 如果需要位置信息来确保唯一性
            if (node.totalSiblings > 1 && !node.attributes.id && !node.attributes.class) {
                cssSelector += `:nth-of-type(${node.position})`;
                xpathSelector += `[${node.position}]`;
            }

            cssPath.push(cssSelector);
            xpathPath.push(xpathSelector);
        }

        return {
            css: cssPath.join(' > '),
            xpath: '//' + xpathPath.join('/')
        };
    }

    // 创建路径描述
    function createPathDescription(pathChain) {
        const description = {
            totalDepth: pathChain.length,
            pathSummary: [],
            uniqueIdentifiers: [],
            structuralInfo: {}
        };

        pathChain.forEach((node, index) => {
            const nodeDesc = {
                level: index + 1,
                tag: node.tagName,
                identifiers: node.uniqueIdentifiers,
                position: `${node.position}/${node.totalSiblings}`,
                isUnique: node.uniqueIdentifiers.length > 0
            };

            description.pathSummary.push(nodeDesc);

            if (node.uniqueIdentifiers.length > 0) {
                description.uniqueIdentifiers.push({
                    level: index + 1,
                    tag: node.tagName,
                    identifiers: node.uniqueIdentifiers
                });
            }
        });

        // 结构信息
        description.structuralInfo = {
            hasUniqueId: pathChain.some(node => node.attributes.id),
            hasStableClasses: pathChain.some(node =>
                node.attributes.class &&
                (node.attributes.class.includes('content') ||
                 node.attributes.class.includes('main') ||
                 node.attributes.class.includes('container'))
            ),
            maxSiblings: Math.max(...pathChain.map(node => node.totalSiblings))
        };

        return JSON.stringify(description, null, 2);
    }

    // 创建简化的页面结构
    function createSimplifiedStructure(container, targetElement) {
        const structure = {
            tagName: container.tagName.toLowerCase(),
            attributes: {},
            children: [],
            isTargetContainer: container.contains(targetElement)
        };

        // 收集容器属性
        const tempAttributes = ['data-selected-original-style', 'style'];
        for (let attr of container.attributes) {
            if (!tempAttributes.includes(attr.name) &&
                !attr.name.includes('selected') &&
                !attr.name.includes('highlight') &&
                !attr.name.includes('outline')) {
                structure.attributes[attr.name] = attr.value;
            }
        }

        // 收集重要的子元素
        Array.from(container.children).forEach((child, index) => {
            if (child.contains(targetElement) || child === targetElement ||
                child.tagName.toLowerCase() === targetElement.tagName.toLowerCase()) {

                const childInfo = {
                    tagName: child.tagName.toLowerCase(),
                    attributes: {},
                    textContent: child.textContent ? child.textContent.trim().substring(0, 200) : '',
                    isTarget: child === targetElement,
                    containsTarget: child.contains(targetElement)
                };

                // 收集子元素属性
                for (let attr of child.attributes) {
                    if (!tempAttributes.includes(attr.name) &&
                        !attr.name.includes('selected') &&
                        !attr.name.includes('highlight') &&
                        !attr.name.includes('outline')) {
                        childInfo.attributes[attr.name] = attr.value;
                    }
                }

                structure.children.push(childInfo);
            }
        });

        return structure;
    }

    // 清理元素属性
    function cleanElementAttributes(element) {
        const tempAttributes = ['data-selected-original-style', 'style'];

        // 清理当前元素
        tempAttributes.forEach(attr => {
            if (element.hasAttribute(attr)) {
                element.removeAttribute(attr);
            }
        });

        // 递归清理子元素
        Array.from(element.children).forEach(child => {
            cleanElementAttributes(child);
        });
    }

    // 收集上下文HTML
    function collectContextHtml(element) {
        let context = [];
        let current = element;
        let depth = 0;
        const maxDepth = 4;

        // 向上收集父元素
        while (current && current !== document.body && depth < maxDepth) {
            const parent = current.parentElement;
            if (parent) {
                // 收集父元素信息
                const parentInfo = {
                    tagName: parent.tagName.toLowerCase(),
                    attributes: {},
                    children: []
                };

                // 收集父元素属性（过滤临时属性）
                const tempAttributes = ['data-selected-original-style', 'style'];
                for (let attr of parent.attributes) {
                    if (!tempAttributes.includes(attr.name) &&
                        !attr.name.includes('selected') &&
                        !attr.name.includes('highlight') &&
                        !attr.name.includes('outline')) {
                        parentInfo.attributes[attr.name] = attr.value;
                    }
                }

                // 收集兄弟元素信息
                Array.from(parent.children).forEach((child, index) => {
                    const childInfo = {
                        tagName: child.tagName.toLowerCase(),
                        attributes: {},
                        textContent: child.textContent ? child.textContent.trim().substring(0, 100) : '',
                        isTarget: child === current
                    };

                    // 收集子元素属性
                    for (let attr of child.attributes) {
                        childInfo.attributes[attr.name] = attr.value;
                    }

                    parentInfo.children.push(childInfo);
                });

                context.unshift(parentInfo);
            }
            current = parent;
            depth++;
        }

        return JSON.stringify(context, null, 2);
    }

    // 显示加载状态
    function showLoadingState() {
        if (popover) {
            const confirmBtn = popover.querySelector('.confirm-btn');
            if (confirmBtn) {
                confirmBtn.disabled = true;
                confirmBtn.textContent = 'AI生成中...';
            }
        }
    }

    // 隐藏加载状态
    function hideLoadingState() {
        if (popover) {
            const confirmBtn = popover.querySelector('.confirm-btn');
            if (confirmBtn) {
                confirmBtn.disabled = false;
                confirmBtn.textContent = '确认选择';
            }
        }
    }
    
    // 根据用户意图生成选择器
    function generateSelectorsWithIntent(element, intent) {
        console.log('Generating selectors with intent:', intent);

        let selectorStrategies;
        let modeRecommend = intent;

        switch (intent) {
            case 'fixed':
                // 固定位置监控：生成最稳定的选择器
                selectorStrategies = generateFixedPositionStrategies(element);
                break;
            case 'latest':
                // 最新内容监控：生成列表第一个元素的选择器
                selectorStrategies = generateLatestContentStrategies(element);
                break;
            case 'list':
                // 列表监控：生成匹配所有列表项的选择器
                selectorStrategies = generateListStrategies(element);
                break;
            default:
                // 默认使用原有逻辑
                selectorStrategies = generateSelectorStrategies(element);
                modeRecommend = inferMode(element);
        }

        const exampleText = element.textContent ? element.textContent.trim().substring(0, 100) : '';

        return {
            css_selector: selectorStrategies.primary.css,
            css_options: selectorStrategies.all.map(s => s.css),
            xpath: selectorStrategies.primary.xpath,
            xpath_options: selectorStrategies.all.map(s => s.xpath),
            mode_recommend: modeRecommend,
            example_text: exampleText,
            tag: element.tagName.toLowerCase(),
            timestamp: Date.now(),
            intent: intent,
            strategies: selectorStrategies.all.map(s => ({
                name: s.name,
                css: s.css,
                xpath: s.xpath,
                description: s.description
            }))
        };
    }

    // 生成选择器（保留原有函数以兼容）
    function generateSelectors(element) {
        return generateSelectorsWithIntent(element, 'auto');
    }

    // 生成固定位置监控策略
    function generateFixedPositionStrategies(element) {
        const strategies = [];

        // 策略1: ID选择器（最稳定）
        if (element.id) {
            strategies.push({
                name: 'id',
                css: `#${element.id}`,
                xpath: `//*[@id="${element.id}"]`,
                description: '基于ID的选择器（最稳定）'
            });
        }

        // 策略2: 数据属性选择器
        const dataAttrs = ['data-id', 'data-key', 'data-testid', 'data-value'];
        for (const attr of dataAttrs) {
            if (element.hasAttribute(attr)) {
                const value = element.getAttribute(attr);
                if (value && value.length < 50) {
                    strategies.push({
                        name: 'data-attribute',
                        css: `[${attr}="${value}"]`,
                        xpath: `//*[@${attr}="${value}"]`,
                        description: `基于${attr}属性的选择器（稳定）`
                    });
                    break;
                }
            }
        }

        // 策略3: 稳定的类名选择器
        if (element.className && typeof element.className === 'string') {
            const classes = element.className.trim().split(/\s+/)
                .filter(c => c && !c.includes('outline') && !c.match(/^(css-|_|sc-)/));

            if (classes.length > 0) {
                const stableClass = classes.find(c =>
                    c.includes('content') || c.includes('title') || c.includes('main')
                ) || classes[0];

                strategies.push({
                    name: 'stable-class',
                    css: `.${stableClass}`,
                    xpath: `//*[contains(@class, "${stableClass}")]`,
                    description: '基于稳定类名的选择器（中等稳定性）'
                });
            }
        }

        // 策略4: 结构化路径选择器
        const structuralSelector = generateStableStructuralSelector(element);
        if (structuralSelector) {
            strategies.push(structuralSelector);
        }

        // 如果没有其他策略，使用基础策略
        if (strategies.length === 0) {
            strategies.push({
                name: 'basic',
                css: element.tagName.toLowerCase(),
                xpath: `//${element.tagName.toLowerCase()}`,
                description: '基础标签选择器（不推荐）'
            });
        }

        return {
            primary: strategies[0],
            all: strategies
        };
    }

    // 生成最新内容监控策略
    function generateLatestContentStrategies(element) {
        const strategies = [];

        // 检查用户是否选择了列表容器
        const isListContainer = isElementListContainer(element);

        if (isListContainer) {
            // 用户选择了列表容器，生成指向第一个子项目的选择器
            const firstChild = getFirstListItem(element);
            if (firstChild) {
                const elementSelector = generateElementSelector(element);
                const elementXPath = generateElementXPath(element);

                strategies.push({
                    name: 'first-child-of-container',
                    css: `${elementSelector} > ${firstChild.tagName.toLowerCase()}:first-child`,
                    xpath: `${elementXPath}/${firstChild.tagName.toLowerCase()}[1]`,
                    description: '列表容器中的第一个元素（推荐用于最新内容）'
                });

                // 备选策略：使用类名选择第一个项目
                if (firstChild.className) {
                    const classes = firstChild.className.trim().split(/\s+/)
                        .filter(c => c && !c.includes('outline') && !c.match(/^(css-|_|sc-)/));

                    if (classes.length > 0) {
                        const itemClass = classes[0];
                        strategies.push({
                            name: 'first-child-by-class',
                            css: `${elementSelector} .${itemClass}:first-child`,
                            xpath: `${elementXPath}//*[contains(@class, "${itemClass}")][1]`,
                            description: '基于类名的第一个列表项'
                        });
                    }
                }
            }
        } else {
            // 用户选择了列表项，使用原有逻辑
            const parent = element.parentElement;

            if (parent) {
                // 分析列表结构
                const siblings = Array.from(parent.children).filter(child =>
                    child.tagName === element.tagName
                );

                if (siblings.length > 1) {
                    const index = siblings.indexOf(element);

                    // 策略1: 第一个子元素选择器
                    if (index === 0) {
                        const parentSelector = generateParentSelector(parent);
                        const parentXPath = generateParentXPath(parent);
                        strategies.push({
                            name: 'first-child',
                            css: `${parentSelector} > ${element.tagName.toLowerCase()}:first-child`,
                            xpath: `${parentXPath}/${element.tagName.toLowerCase()}[1]`,
                            description: '列表第一个元素（推荐用于最新内容）'
                        });
                    }

                    // 策略2: nth-child选择器（如果不是第一个）
                    const parentSelector = generateParentSelector(parent);
                    const parentXPath = generateParentXPath(parent);
                    strategies.push({
                        name: 'nth-child',
                        css: `${parentSelector} > ${element.tagName.toLowerCase()}:nth-child(${index + 1})`,
                        xpath: `${parentXPath}/${element.tagName.toLowerCase()}[${index + 1}]`,
                        description: `列表第${index + 1}个元素`
                    });
                }
            }
        }

        // 如果没有找到列表结构，回退到固定位置策略
        if (strategies.length === 0) {
            return generateFixedPositionStrategies(element);
        }

        return {
            primary: strategies[0],
            all: strategies
        };
    }

    // 生成列表监控策略
    function generateListStrategies(element) {
        const strategies = [];
        const parent = element.parentElement;

        if (parent) {
            // 策略1: 匹配所有同类型兄弟元素
            const parentSelector = generateParentSelector(parent);
            strategies.push({
                name: 'all-siblings',
                css: `${parentSelector} > ${element.tagName.toLowerCase()}`,
                xpath: `${generateParentXPath(parent)}/${element.tagName.toLowerCase()}`,
                description: '列表中所有同类型元素'
            });

            // 策略2: 基于类名匹配所有列表项
            if (element.className && typeof element.className === 'string') {
                const classes = element.className.trim().split(/\s+/)
                    .filter(c => c && !c.includes('outline') && !c.match(/^(css-|_|sc-)/));

                if (classes.length > 0) {
                    const itemClass = classes.find(c =>
                        c.includes('item') || c.includes('entry') || c.includes('row')
                    ) || classes[0];

                    strategies.push({
                        name: 'class-based',
                        css: `.${itemClass}`,
                        xpath: `//*[contains(@class, "${itemClass}")]`,
                        description: '基于类名匹配所有列表项'
                    });
                }
            }
        }

        // 如果没有找到列表结构，回退到固定位置策略
        if (strategies.length === 0) {
            return generateFixedPositionStrategies(element);
        }

        return {
            primary: strategies[0],
            all: strategies
        };
    }

    // 生成多种选择器策略
    function generateSelectorStrategies(element) {
        const strategies = [];

        // 策略1: 精确位置选择器（最适合监控最新内容）
        const precisePositionStrategy = generatePrecisePositionStrategy(element);
        if (precisePositionStrategy) {
            strategies.push(precisePositionStrategy);
        }

        // 策略2: 属性选择器（最稳定）
        const attributeStrategy = generateAttributeStrategy(element);
        if (attributeStrategy) {
            strategies.push(attributeStrategy);
        }

        // 策略3: 类名选择器（中等稳定性）
        const classStrategy = generateClassStrategy(element);
        if (classStrategy) {
            strategies.push(classStrategy);
        }

        // 策略4: 结构化路径选择器（适合复杂页面）
        const structuralStrategy = generateStructuralStrategy(element);
        if (structuralStrategy) {
            strategies.push(structuralStrategy);
        }

        // 策略5: 文本内容选择器（适合固定文本）
        const textStrategy = generateTextStrategy(element);
        if (textStrategy) {
            strategies.push(textStrategy);
        }

        // 如果没有其他策略，使用基础策略
        if (strategies.length === 0) {
            strategies.push({
                name: 'basic',
                css: element.tagName.toLowerCase(),
                xpath: `//${element.tagName.toLowerCase()}`,
                description: '基础标签选择器（不推荐，会匹配多个元素）'
            });
        }

        return {
            primary: strategies[0],
            all: strategies
        };
    }

    // 生成精确位置策略（专门用于监控最新内容）
    function generatePrecisePositionStrategy(element) {
        const parent = element.parentElement;
        if (!parent) return null;

        const siblings = Array.from(parent.children).filter(child =>
            child.tagName === element.tagName
        );

        if (siblings.length <= 1) return null;

        const index = siblings.indexOf(element);

        // 构建父元素的精确路径
        const parentPath = buildPrecisePath(parent);

        if (index === 0) {
            return {
                name: 'first-item',
                css: `${parentPath} > ${element.tagName.toLowerCase()}:first-child`,
                xpath: `${buildXPathPath(parent)}/${element.tagName.toLowerCase()}[1]`,
                description: '第一个项目（适合监控最新内容）'
            };
        } else if (index === siblings.length - 1) {
            return {
                name: 'last-item',
                css: `${parentPath} > ${element.tagName.toLowerCase()}:last-child`,
                xpath: `${buildXPathPath(parent)}/${element.tagName.toLowerCase()}[last()]`,
                description: '最后一个项目'
            };
        } else {
            return {
                name: 'nth-item',
                css: `${parentPath} > ${element.tagName.toLowerCase()}:nth-child(${index + 1})`,
                xpath: `${buildXPathPath(parent)}/${element.tagName.toLowerCase()}[${index + 1}]`,
                description: `第${index + 1}个项目（固定位置）`
            };
        }
    }

    // 构建精确的CSS路径
    function buildPrecisePath(element, maxDepth = 3) {
        const path = [];
        let current = element;
        let depth = 0;

        while (current && current !== document.body && depth < maxDepth) {
            let selector = current.tagName.toLowerCase();

            // 添加ID
            if (current.id) {
                selector = `#${current.id}`;
                path.unshift(selector);
                break;
            }

            // 添加有意义的类名
            if (current.className && typeof current.className === 'string') {
                const classes = current.className.trim().split(/\s+/)
                    .filter(c => c &&
                        !c.includes('outline') &&
                        !c.match(/^(css-|_|sc-)/));

                if (classes.length > 0) {
                    const bestClass = classes.find(c =>
                        c.includes('content') ||
                        c.includes('section') ||
                        c.includes('list') ||
                        c.includes('container')
                    ) || classes[0];

                    selector += `.${bestClass}`;
                }
            }

            path.unshift(selector);
            current = current.parentElement;
            depth++;
        }

        return path.join(' ');
    }

    // 构建XPath路径
    function buildXPathPath(element, maxDepth = 3) {
        const path = [];
        let current = element;
        let depth = 0;

        while (current && current !== document.body && depth < maxDepth) {
            if (current.id) {
                return `//*[@id="${current.id}"]`;
            }

            const tagName = current.tagName.toLowerCase();
            const siblings = Array.from(current.parentNode?.children || [])
                .filter(sibling => sibling.tagName === current.tagName);

            if (siblings.length === 1) {
                path.unshift(tagName);
            } else {
                const index = siblings.indexOf(current) + 1;
                path.unshift(`${tagName}[${index}]`);
            }

            current = current.parentElement;
            depth++;
        }

        return '//' + path.join('/');
    }

    // 生成属性策略
    function generateAttributeStrategy(element) {
        const meaningfulAttrs = ['data-id', 'data-key', 'data-testid', 'name', 'role', 'href'];

        for (const attr of meaningfulAttrs) {
            if (element.hasAttribute(attr)) {
                const value = element.getAttribute(attr);
                if (value && value.length < 100) {
                    return {
                        name: 'attribute',
                        css: `[${attr}="${value}"]`,
                        xpath: `//*[@${attr}="${value}"]`,
                        description: `基于${attr}属性（最稳定）`
                    };
                }
            }
        }

        return null;
    }

    // 生成类名策略
    function generateClassStrategy(element) {
        if (!element.className || typeof element.className !== 'string') {
            return null;
        }

        const classes = element.className.trim().split(/\s+/)
            .filter(c => c &&
                !c.includes('outline') &&
                !c.match(/^(css-|_|sc-)/));

        if (classes.length === 0) return null;

        // 寻找最有意义的类名
        const bestClass = classes.find(c =>
            c.includes('item') ||
            c.includes('entry') ||
            c.includes('post') ||
            c.includes('article') ||
            c.includes('content')
        ) || classes[0];

        return {
            name: 'class',
            css: `.${bestClass}`,
            xpath: `//*[contains(@class, "${bestClass}")]`,
            description: `基于类名（中等稳定性）`
        };
    }

    // 生成结构化策略
    function generateStructuralStrategy(element) {
        const path = buildPrecisePath(element, 4);
        const xpathPath = buildXPathPath(element, 4);

        if (path && path.split(' ').length > 1) {
            return {
                name: 'structural',
                css: path,
                xpath: xpathPath,
                description: '基于页面结构（适合复杂页面）'
            };
        }

        return null;
    }

    // 生成文本策略
    function generateTextStrategy(element) {
        const text = element.textContent?.trim();
        if (!text || text.length > 50) return null;

        // 检查文本是否在页面中唯一
        const elementsWithSameText = Array.from(document.querySelectorAll(element.tagName))
            .filter(el => el.textContent?.trim() === text);

        if (elementsWithSameText.length === 1) {
            const escapedText = text.replace(/"/g, '\\"');
            return {
                name: 'text',
                css: `${element.tagName.toLowerCase()}`, // CSS不支持文本选择，这里只是标记
                xpath: `//${element.tagName.toLowerCase()}[normalize-space(text())="${escapedText}"]`,
                description: `基于文本内容（仅XPath可用）`
            };
        }

        return null;
    }
    
    // 生成CSS选择器
    function generateCSSSelector(element) {
        // 优先使用ID
        if (element.id) {
            return `#${element.id}`;
        }

        // 分析元素的上下文，生成更智能的选择器
        const selectors = [];

        // 1. 尝试使用有意义的属性
        const meaningfulAttrs = ['data-id', 'data-key', 'data-value', 'data-testid', 'name', 'role'];
        for (const attr of meaningfulAttrs) {
            if (element.hasAttribute(attr)) {
                const value = element.getAttribute(attr);
                if (value && value.length < 50) {
                    selectors.push(`[${attr}="${value}"]`);
                }
            }
        }

        // 2. 分析类名，选择有意义的类
        if (element.className && typeof element.className === 'string') {
            const classes = element.className.trim().split(/\s+/)
                .filter(c => c &&
                    !c.includes('outline') &&
                    !c.includes('style') &&
                    !c.includes('color') &&
                    !c.match(/^(css-|_|sc-)/)); // 过滤CSS-in-JS生成的类名

            if (classes.length > 0) {
                // 优先使用看起来有语义的类名
                const semanticClasses = classes.filter(c =>
                    c.includes('item') ||
                    c.includes('list') ||
                    c.includes('content') ||
                    c.includes('title') ||
                    c.includes('link') ||
                    c.length > 3
                );

                if (semanticClasses.length > 0) {
                    selectors.push(`.${semanticClasses[0]}`);
                    selectors.push(`${element.tagName.toLowerCase()}.${semanticClasses[0]}`);
                } else if (classes.length > 0) {
                    selectors.push(`.${classes[0]}`);
                }
            }
        }

        // 3. 生成基于结构的选择器
        const structuralSelector = generateStructuralSelector(element);
        if (structuralSelector) {
            selectors.push(structuralSelector);
        }

        // 4. 生成基于位置的选择器
        const positionSelector = generatePositionSelector(element);
        if (positionSelector) {
            selectors.push(positionSelector);
        }

        // 返回最佳选择器
        return selectors[0] || element.tagName.toLowerCase();
    }

    // 生成结构化选择器
    function generateStructuralSelector(element) {
        const path = [];
        let current = element;
        let depth = 0;

        while (current && current !== document.body && depth < 3) {
            let selector = current.tagName.toLowerCase();

            // 添加有意义的类名
            if (current.className && typeof current.className === 'string') {
                const classes = current.className.trim().split(/\s+/)
                    .filter(c => c &&
                        !c.includes('outline') &&
                        !c.match(/^(css-|_|sc-)/));

                if (classes.length > 0) {
                    const bestClass = classes.find(c =>
                        c.includes('item') ||
                        c.includes('list') ||
                        c.includes('content')
                    ) || classes[0];

                    selector += `.${bestClass}`;
                }
            }

            path.unshift(selector);
            current = current.parentElement;
            depth++;
        }

        return path.length > 1 ? path.join(' ') : null;
    }

    // 生成稳定的结构化选择器
    function generateStableStructuralSelector(element) {
        const path = [];
        let current = element;
        let depth = 0;

        while (current && current !== document.body && depth < 4) {
            let selector = current.tagName.toLowerCase();

            // 优先使用ID
            if (current.id) {
                selector = `#${current.id}`;
                path.unshift(selector);
                break;
            }

            // 使用稳定的类名
            if (current.className && typeof current.className === 'string') {
                const classes = current.className.trim().split(/\s+/)
                    .filter(c => c && !c.includes('outline') && !c.match(/^(css-|_|sc-)/));

                const stableClass = classes.find(c =>
                    c.includes('content') || c.includes('main') || c.includes('container')
                );

                if (stableClass) {
                    selector += `.${stableClass}`;
                }
            }

            path.unshift(selector);
            current = current.parentElement;
            depth++;
        }

        if (path.length > 1) {
            return {
                name: 'structural',
                css: path.join(' > '),
                xpath: '//' + path.join('/'),
                description: '基于稳定结构的选择器'
            };
        }

        return null;
    }

    // 生成父元素选择器
    function generateParentSelector(parent) {
        if (parent.id) {
            return `#${parent.id}`;
        }

        if (parent.className && typeof parent.className === 'string') {
            const classes = parent.className.trim().split(/\s+/)
                .filter(c => c && !c.includes('outline') && !c.match(/^(css-|_|sc-)/));

            if (classes.length > 0) {
                const bestClass = classes.find(c =>
                    c.includes('list') || c.includes('container') || c.includes('items')
                ) || classes[0];

                return `${parent.tagName.toLowerCase()}.${bestClass}`;
            }
        }

        return parent.tagName.toLowerCase();
    }

    // 生成父元素XPath
    function generateParentXPath(parent) {
        // 构建到父元素的完整路径
        const path = [];
        let current = parent;
        let depth = 0;

        while (current && current !== document.body && depth < 5) {
            let selector = current.tagName.toLowerCase();

            // 如果有ID，直接使用ID并停止向上查找
            if (current.id) {
                path.unshift(`*[@id="${current.id}"]`);
                break;
            }

            // 如果有有意义的类名，使用类名
            if (current.className && typeof current.className === 'string') {
                const classes = current.className.trim().split(/\s+/)
                    .filter(c => c && !c.includes('outline') && !c.match(/^(css-|_|sc-)/));

                if (classes.length > 0) {
                    const bestClass = classes.find(c =>
                        c.includes('list') || c.includes('container') || c.includes('items')
                    ) || classes[0];

                    selector = `${selector}[contains(@class, "${bestClass}")]`;
                }
            }

            // 添加位置信息以确保唯一性
            const siblings = Array.from(current.parentNode?.children || [])
                .filter(sibling => sibling.tagName === current.tagName);

            if (siblings.length > 1) {
                const index = siblings.indexOf(current) + 1;
                selector = `${selector}[${index}]`;
            }

            path.unshift(selector);
            current = current.parentElement;
            depth++;
        }

        return '//' + path.join('/');
    }

    // 检查元素是否为列表容器
    function isElementListContainer(element) {
        const tagName = element.tagName.toLowerCase();

        // 检查标签类型
        if (tagName === 'ul' || tagName === 'ol' || tagName === 'dl') {
            return true;
        }

        // 检查类名是否包含列表相关的词汇
        if (element.className && typeof element.className === 'string') {
            const className = element.className.toLowerCase();
            if (className.includes('list') || className.includes('items') ||
                className.includes('entries') || className.includes('feed')) {
                return true;
            }
        }

        // 检查是否有多个相似的子元素
        const children = Array.from(element.children);
        if (children.length > 1) {
            const firstChildTag = children[0].tagName;
            const sameTagChildren = children.filter(child => child.tagName === firstChildTag);
            if (sameTagChildren.length >= 2) {
                return true;
            }
        }

        return false;
    }

    // 获取列表容器中的第一个列表项
    function getFirstListItem(container) {
        const children = Array.from(container.children);
        if (children.length === 0) return null;

        // 对于标准列表，返回第一个子元素
        if (container.tagName.toLowerCase() === 'ul' || container.tagName.toLowerCase() === 'ol') {
            return children[0];
        }

        // 对于其他容器，找到最常见的子元素类型
        const tagCounts = {};
        children.forEach(child => {
            const tag = child.tagName.toLowerCase();
            tagCounts[tag] = (tagCounts[tag] || 0) + 1;
        });

        const mostCommonTag = Object.keys(tagCounts).reduce((a, b) =>
            tagCounts[a] > tagCounts[b] ? a : b
        );

        return children.find(child => child.tagName.toLowerCase() === mostCommonTag);
    }

    // 生成元素选择器
    function generateElementSelector(element) {
        if (element.id) {
            return `#${element.id}`;
        }

        if (element.className && typeof element.className === 'string') {
            const classes = element.className.trim().split(/\s+/)
                .filter(c => c && !c.includes('outline') && !c.match(/^(css-|_|sc-)/));

            if (classes.length > 0) {
                const bestClass = classes.find(c =>
                    c.includes('list') || c.includes('container') || c.includes('items')
                ) || classes[0];

                return `${element.tagName.toLowerCase()}.${bestClass}`;
            }
        }

        return element.tagName.toLowerCase();
    }

    // 生成元素XPath
    function generateElementXPath(element) {
        if (element.id) {
            return `//*[@id="${element.id}"]`;
        }

        if (element.className && typeof element.className === 'string') {
            const classes = element.className.trim().split(/\s+/)
                .filter(c => c && !c.includes('outline') && !c.match(/^(css-|_|sc-)/));

            if (classes.length > 0) {
                const bestClass = classes.find(c =>
                    c.includes('list') || c.includes('container') || c.includes('items')
                ) || classes[0];

                return `//${element.tagName.toLowerCase()}[contains(@class, "${bestClass}")]`;
            }
        }

        // 生成基于位置的XPath
        const parent = element.parentElement;
        if (parent) {
            const siblings = Array.from(parent.children).filter(child =>
                child.tagName === element.tagName
            );

            if (siblings.length > 1) {
                const index = siblings.indexOf(element) + 1;
                const parentXPath = generateParentXPath(parent);
                return `${parentXPath}/${element.tagName.toLowerCase()}[${index}]`;
            }
        }

        return `//${element.tagName.toLowerCase()}`;
    }

    // 生成基于位置的选择器
    function generatePositionSelector(element) {
        const parent = element.parentElement;
        if (!parent) return null;

        const siblings = Array.from(parent.children).filter(child =>
            child.tagName === element.tagName
        );

        if (siblings.length <= 1) {
            return element.tagName.toLowerCase();
        }

        const index = siblings.indexOf(element);

        // 如果是第一个或最后一个，使用更语义化的选择器
        if (index === 0) {
            return `${element.tagName.toLowerCase()}:first-child`;
        } else if (index === siblings.length - 1) {
            return `${element.tagName.toLowerCase()}:last-child`;
        } else {
            return `${element.tagName.toLowerCase()}:nth-child(${index + 1})`;
        }
    }
    
    // 生成XPath
    function generateXPath(element) {
        // 优先使用ID
        if (element.id) {
            return `//*[@id="${element.id}"]`;
        }

        // 尝试使用有意义的属性
        const meaningfulAttrs = ['data-id', 'data-key', 'data-testid', 'name', 'role'];
        for (const attr of meaningfulAttrs) {
            if (element.hasAttribute(attr)) {
                const value = element.getAttribute(attr);
                if (value && value.length < 50) {
                    return `//*[@${attr}="${value}"]`;
                }
            }
        }

        // 尝试使用类名（选择有意义的类）
        if (element.className && typeof element.className === 'string') {
            const classes = element.className.trim().split(/\s+/)
                .filter(c => c &&
                    !c.includes('outline') &&
                    !c.match(/^(css-|_|sc-)/));

            if (classes.length > 0) {
                const bestClass = classes.find(c =>
                    c.includes('item') ||
                    c.includes('list') ||
                    c.includes('content') ||
                    c.includes('title')
                ) || classes[0];

                return `//${element.tagName.toLowerCase()}[contains(@class, "${bestClass}")]`;
            }
        }

        // 生成基于位置的XPath
        const parent = element.parentElement;
        if (parent) {
            const siblings = Array.from(parent.children).filter(child =>
                child.tagName === element.tagName
            );

            if (siblings.length === 1) {
                // 如果是唯一的同类型元素
                return `//${element.tagName.toLowerCase()}`;
            } else {
                const index = siblings.indexOf(element) + 1;

                // 使用更语义化的位置表达式
                if (index === 1) {
                    return `//${element.tagName.toLowerCase()}[1]`;
                } else if (index === siblings.length) {
                    return `//${element.tagName.toLowerCase()}[last()]`;
                } else {
                    return `//${element.tagName.toLowerCase()}[${index}]`;
                }
            }
        }

        // 生成简单的相对路径XPath（最多2层）
        const path = [];
        let current = element;
        let depth = 0;

        while (current && current !== document.body && depth < 2) {
            const tagName = current.tagName.toLowerCase();
            const siblings = Array.from(current.parentNode?.children || [])
                .filter(sibling => sibling.tagName === current.tagName);

            if (siblings.length === 1) {
                path.unshift(tagName);
            } else {
                const index = siblings.indexOf(current) + 1;
                path.unshift(`${tagName}[${index}]`);
            }

            current = current.parentElement;
            depth++;
        }

        return '//' + path.join('/');
    }
    
    // 推断模式
    function inferMode(element) {
        const parent = element.parentElement;
        if (!parent) return 'fixed';
        
        // 检查是否在列表中
        const siblings = Array.from(parent.children).filter(child => 
            child.tagName === element.tagName && 
            child.className === element.className
        );
        
        if (siblings.length > 1) {
            const index = siblings.indexOf(element);
            if (index === siblings.length - 1) {
                return 'latest'; // 最新一条
            } else {
                return 'list'; // 列表中的一项
            }
        }
        
        return 'fixed'; // 固定区域
    }
    
    // 发送结果到父窗口
    function sendResultToParent(result) {
        try {
            window.parent.postMessage({
                type: 'SELECTOR_RESULT',
                data: result
            }, '*');
            console.log('Selector result sent to parent:', result);
        } catch (error) {
            console.error('Error sending result to parent:', error);
        }
    }
    
    // 停用选择器
    function deactivate() {
        isActive = false;
        clearHighlight();
        deselectElement();
        
        // 移除事件监听器
        document.removeEventListener('mouseover', handleMouseOver, true);
        document.removeEventListener('mouseout', handleMouseOut, true);
        document.removeEventListener('click', handleClick, true);
        document.removeEventListener('keydown', handleKeyDown, true);
        
        console.log('Element selector deactivated');
    }
    
    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
})();
