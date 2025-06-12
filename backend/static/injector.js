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
                padding: 10px;
                z-index: 10000;
                font-family: Arial, sans-serif;
                font-size: 12px;
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

        // 如果点击的是弹窗内的按钮，检查是否是确认或重选按钮
        const popoverElement = element.closest('.selector-popover');
        if (popoverElement) {
            console.log('Click on popover element:', element);
            // 如果是确认或重选按钮，不要阻止事件，让它正常传播
            if (element.classList.contains('confirm-btn') || element.classList.contains('reselect-btn')) {
                console.log('Click on popover button, not preventing default');
                // 不要preventDefault和stopPropagation，让按钮的事件监听器正常工作
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
        
        // 显示弹窗
        showPopover(element);
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
        
        popover = document.createElement('div');
        popover.className = 'selector-popover';
        popover.innerHTML = `
            <div>已选择元素: ${element.tagName.toLowerCase()}</div>
            <div style="margin: 5px 0;">
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

        if (confirmBtn) {
            console.log('Adding click listener to confirm button');
            confirmBtn.addEventListener('click', function(e) {
                console.log('Confirm button clicked!');
                e.preventDefault();
                e.stopPropagation();
                confirmSelection();
            });
        }

        if (reselectBtn) {
            console.log('Adding click listener to reselect button');
            reselectBtn.addEventListener('click', function(e) {
                console.log('Reselect button clicked!');
                e.preventDefault();
                e.stopPropagation();
                reselectElement();
            });
        }
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
    function confirmSelection() {
        console.log('confirmSelection called, selectedElement:', selectedElement);
        if (!selectedElement) {
            console.error('No element selected');
            return;
        }

        const result = generateSelectors(selectedElement);
        console.log('Generated selectors:', result);
        sendResultToParent(result);

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
    
    // 生成选择器
    function generateSelectors(element) {
        // 生成多种选择器策略
        const selectorStrategies = generateSelectorStrategies(element);

        const modeRecommend = inferMode(element);
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
            strategies: selectorStrategies.all.map(s => ({
                name: s.name,
                css: s.css,
                xpath: s.xpath,
                description: s.description
            }))
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
