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
        const cssSelector = generateCSSSelector(element);
        const xpath = generateXPath(element);
        const modeRecommend = inferMode(element);
        const exampleText = element.textContent ? element.textContent.trim().substring(0, 100) : '';
        
        return {
            css_selector: cssSelector,
            xpath: xpath,
            mode_recommend: modeRecommend,
            example_text: exampleText,
            tag: element.tagName.toLowerCase(),
            timestamp: Date.now()
        };
    }
    
    // 生成CSS选择器
    function generateCSSSelector(element) {
        // 优先使用ID
        if (element.id) {
            return `#${element.id}`;
        }
        
        // 构建路径
        const path = [];
        let current = element;
        
        while (current && current !== document.body) {
            let selector = current.tagName.toLowerCase();
            
            // 添加类名
            if (current.className && typeof current.className === 'string') {
                const classes = current.className.trim().split(/\s+/).filter(c => c);
                if (classes.length > 0) {
                    selector += '.' + classes.join('.');
                }
            }
            
            // 添加nth-child如果需要
            const siblings = Array.from(current.parentNode?.children || [])
                .filter(sibling => sibling.tagName === current.tagName);
            
            if (siblings.length > 1) {
                const index = siblings.indexOf(current) + 1;
                selector += `:nth-child(${index})`;
            }
            
            path.unshift(selector);
            current = current.parentElement;
        }
        
        return path.join(' > ');
    }
    
    // 生成XPath
    function generateXPath(element) {
        const path = [];
        let current = element;
        
        while (current && current !== document) {
            let index = 1;
            let sibling = current.previousSibling;
            
            while (sibling) {
                if (sibling.nodeType === 1 && sibling.tagName === current.tagName) {
                    index++;
                }
                sibling = sibling.previousSibling;
            }
            
            const tagName = current.tagName.toLowerCase();
            path.unshift(`${tagName}[${index}]`);
            current = current.parentElement;
        }
        
        return '/' + path.join('/');
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
