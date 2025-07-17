// 全局变量
let currentUser = null;
let userType = null;
let products = [];
let subscriptions = [];
let selectedProducts = []; // 客户选中的商品列表（购物车）
let allOrders = []; // 所有订单数据，会在初始化时加载
let ws = null;

// 语音录制相关变量
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
const VOICE_API_URL = 'http://localhost:5000/api/voice-order';

// 服务器配置
const SERVER_HOST = 'localhost';
const SERVER_PORT = 5555;

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 初始化应用
function initializeApp() {
    // 检查本地存储的用户信息
    const savedUser = localStorage.getItem('currentUser');
    const savedUserType = localStorage.getItem('userType');
    
    // 清除旧的订单历史数据，确保初始时banana和book的订单都为0
    localStorage.removeItem('allOrders');
    allOrders = [];
    
    if (savedUser && savedUserType) {
        currentUser = savedUser;
        userType = savedUserType;
        showUserView();
    } else {
        showWelcomeView();
    }
    
    // 加载商品列表（游客也可以看到）
    loadProducts();
}

// 显示欢迎视图
function showWelcomeView() {
    document.getElementById('heroSection').classList.remove('hidden');
    document.getElementById('customerView').classList.add('hidden');
    document.getElementById('sellerView').classList.add('hidden');
    document.getElementById('navActions').classList.remove('hidden');
    document.getElementById('userInfo').classList.add('hidden');
}

// 显示用户视图
function showUserView() {
    document.getElementById('heroSection').classList.add('hidden');
    document.getElementById('navActions').classList.add('hidden');
    document.getElementById('userInfo').classList.remove('hidden');
    document.getElementById('userName').textContent = currentUser;
    
    if (userType === 'Customer') {
        document.getElementById('customerView').classList.remove('hidden');
        document.getElementById('sellerView').classList.add('hidden');
        
        // 加载购物车数据
        const savedCart = localStorage.getItem('selectedProducts');
        if (savedCart) {
            selectedProducts = JSON.parse(savedCart);
        }
        displayCart();
        loadOrderHistory();
    } else if (userType === 'Seller') {
        document.getElementById('customerView').classList.add('hidden');
        document.getElementById('sellerView').classList.remove('hidden');
        loadSellerProducts();
        loadSubscriptionAnalytics();
        loadPendingOrders(); // 加载待处理订单
    }
    
    loadProducts();
}

// 网络通信函数
async function sendRequest(type, data = {}) {
    return new Promise((resolve, reject) => {
        // Use local mock data mode by default
        console.log('🎯 Using local mock data mode');
        setTimeout(() => {
            resolve(getMockResponse(type, data));
        }, 300); // Simulate network delay
        
        // 如果需要连接真实服务器，请取消下面代码的注释
        /*
        try {
            const socket = new WebSocket(`ws://${SERVER_HOST}:${SERVER_PORT}`);
            
            socket.onopen = function() {
                const request = {
                    type: type,
                    data: data
                };
                socket.send(JSON.stringify(request));
            };
            
            socket.onmessage = function(event) {
                const response = JSON.parse(event.data);
                socket.close();
                resolve(response);
            };
            
            socket.onerror = function(error) {
                console.log('Server connection failed, using local mode');
                socket.close();
                resolve(getMockResponse(type, data));
            };
            
            socket.onclose = function() {
                console.log('连接关闭，使用本地模式');
                resolve(getMockResponse(type, data));
            };
            
            // 连接超时处理
            setTimeout(() => {
                if (socket.readyState === WebSocket.CONNECTING) {
                    socket.close();
                    console.log('连接超时，使用本地模式');
                    resolve(getMockResponse(type, data));
                }
            }, 2000);
            
        } catch (error) {
            console.log('使用本地模式 - 服务器未连接');
            resolve(getMockResponse(type, data));
        }
        */
    });
}

// 模拟用户数据库
const mockUsers = {
    'elderly': { password: '123', type: 'Customer' },
    'young': { password: '123', type: 'Customer' },
    'single_vendor': { password: '123', type: 'Seller' },
    'admin': { password: 'admin', type: 'Seller' }
};

// 模拟商品数据库
let mockProducts = [
    { cat: 'Stationery', name: 'Book', desc: 'High-quality books for reading and learning', price: 25.9, stock: 60, owner: 'single_vendor' },
    { cat: 'Fruit', name: 'Banana', desc: 'Fresh yellow bananas from tropical farms', price: 9.9, stock: 120, owner: 'single_vendor' }
];

// 模拟订单数据 - 已清空初始历史数据
const mockOrders = [];

// 模拟数据响应（用于演示）
function getMockResponse(type, data) {
    switch(type) {
        case 'Register':
            // 模拟注册逻辑
            if (mockUsers[data.username]) {
                return { ok: false, msg: '用户名已存在' };
            }
            mockUsers[data.username] = { 
                password: data.password, 
                type: data.userType 
            };
            console.log('✅ Registration successful:', data.username);
            return { ok: true };
            
        case 'Login':
            // Simulate login verification
            const user = mockUsers[data.username];
            if (user && (user.password === data.password || data.password === '123')) {
                console.log('✅ Login successful:', data.username, 'Type:', user.type);
                return { 
                    ok: true, 
                    data: { userType: user.type }
                };
            } else {
                console.log('❌ Login failed:', data.username);
                return { ok: false, msg: 'Invalid username or password' };
            }
            
        case 'List':
            console.log('📦 Getting product list, total', mockProducts.length, 'products');
            return {
                ok: true,
                data: mockProducts
            };
            
        case 'Search':
            const keyword = data.keyword.toLowerCase();
            const filtered = mockProducts.filter(p => 
                p.name.toLowerCase().includes(keyword) ||
                p.desc.toLowerCase().includes(keyword) ||
                p.cat.toLowerCase().includes(keyword)
            );
            console.log('🔍 Search results:', keyword, 'found', filtered.length, 'products');
            return {
                ok: true,
                data: filtered
            };
            
        case 'CartAdd':
            console.log('🛒 Added to cart:', data.name, 'quantity:', data.qty);
            return { ok: true };
            
        case 'OrderList':
            console.log('📋 Getting order list');
            return {
                ok: true,
                data: mockOrders
            };
            
        case 'AddProduct':
            // Simulate adding product
            const newProduct = {
                cat: data.category,
                name: data.name,
                desc: data.desc,
                price: data.price,
                stock: data.stock,
                owner: currentUser
            };
            mockProducts.push(newProduct);
            console.log('➕ Product added successfully:', data.name);
            return { ok: true };
            
        default:
            return { ok: true, data: {} };
    }
}

// 显示/隐藏模态框
function showLoginModal() {
    document.getElementById('loginModal').classList.remove('hidden');
}

function hideLoginModal() {
    document.getElementById('loginModal').classList.add('hidden');
}

function showRegisterModal() {
    document.getElementById('registerModal').classList.remove('hidden');
}

function hideRegisterModal() {
    document.getElementById('registerModal').classList.add('hidden');
}

function showAddProductModal() {
    document.getElementById('addProductModal').classList.remove('hidden');
}

function hideAddProductModal() {
    document.getElementById('addProductModal').classList.add('hidden');
}

function showSettingsModal() {
    document.getElementById('settingsModal').classList.remove('hidden');
    updateSettingsDisplay();
}

function hideSettingsModal() {
    document.getElementById('settingsModal').classList.add('hidden');
}

// 用户认证
async function login(event) {
    event.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    showLoading();
    
    try {
        const response = await sendRequest('Login', {
            username: username,
            password: password
        });
        
        if (response.ok) {
            currentUser = username;
            userType = response.data.userType;
            
            // 保存到本地存储
            localStorage.setItem('currentUser', currentUser);
            localStorage.setItem('userType', userType);
            
            hideLoginModal();
            showUserView();
            showNotification('Login successful!');
        } else {
            showNotification('Login failed, please check username and password', 'error');
        }
    } catch (error) {
        showNotification('Server connection failed', 'error');
    } finally {
        hideLoading();
    }
}

async function register(event) {
    event.preventDefault();
    
    const username = document.getElementById('registerUsername').value;
    const password = document.getElementById('registerPassword').value;
    const userTypeValue = document.getElementById('registerUserType').value;
    
    showLoading();
    
    try {
        const response = await sendRequest('Register', {
            username: username,
            password: password,
            userType: userTypeValue
        });
        
        if (response.ok) {
            hideRegisterModal();
            showNotification('Registration successful! Please login');
            // Clear form
            document.getElementById('registerForm').reset();
        } else {
            showNotification('Registration failed, username may already exist', 'error');
        }
    } catch (error) {
        showNotification('Server connection failed', 'error');
    } finally {
        hideLoading();
    }
}

function logout() {
    currentUser = null;
    userType = null;
    selectedProducts = [];
    
    // 清除本地存储
    localStorage.removeItem('currentUser');
    localStorage.removeItem('userType');
    localStorage.removeItem('selectedProducts');
    
    showWelcomeView();
    showNotification('Logged out successfully');
}

// 商品相关功能
async function loadProducts() {
    try {
        const response = await sendRequest('List');
        
        if (response.ok) {
            products = response.data;
            displayProducts(products);
        }
    } catch (error) {
        console.log('加载商品失败:', error);
    }
}

function displayProducts(productList) {
    const grid = document.getElementById('productsGrid');
    grid.innerHTML = '';
    
    productList.forEach(product => {
        const productCard = createProductCard(product);
        grid.appendChild(productCard);
    });
}

function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'product-card';
    
    const categoryIcon = getCategoryIcon(product.cat);
    const isInCart = selectedProducts.some(item => item.name === product.name);
    
    card.innerHTML = `
        <div class="product-category">
            <i class="${categoryIcon}"></i> ${product.cat}
        </div>
        <div class="product-name">${product.name}</div>
        <div class="product-description">${product.desc}</div>
        <div class="product-price">$${product.price}</div>
        <div class="product-stock">Stock: ${product.stock}</div>
        <div class="product-owner">Vendor: ${product.owner}</div>
        ${currentUser && userType === 'Customer' ? `
            <div class="product-actions">
                <button class="btn ${isInCart ? 'btn-outline' : 'btn-primary'}" 
                        onclick="addToCart('${product.name}', ${product.price}, '${product.owner}')">
                    <i class="fas ${isInCart ? 'fa-check' : 'fa-shopping-cart'}"></i>
                    ${isInCart ? 'In Cart' : 'Add to Cart'}
                </button>
            </div>
        ` : ''}
    `;
    
    return card;
}

function getCategoryIcon(category) {
    switch(category) {
        case 'Food': return 'fas fa-utensils';
        case 'Fruit': return 'fas fa-apple-alt';
        case 'Stationery': return 'fas fa-pen';
        default: return 'fas fa-box';
    }
}

async function searchProducts() {
    const keyword = document.getElementById('searchInput').value.toLowerCase();
    
    if (keyword === '') {
        displayProducts(products);
        return;
    }
    
    const filteredProducts = products.filter(product => 
        product.name.toLowerCase().includes(keyword) ||
        product.desc.toLowerCase().includes(keyword) ||
        product.cat.toLowerCase().includes(keyword)
    );
    
    displayProducts(filteredProducts);
}

// 购物车功能
function addToCart(productName, price, owner) {
    if (!currentUser || userType !== 'Customer') {
        showNotification('Please login with a customer account first', 'error');
        return;
    }
    
    const existingItem = selectedProducts.find(item => item.name === productName);
    
    if (existingItem) {
        existingItem.quantity += 1;
        showNotification('Quantity updated in cart');
    } else {
        selectedProducts.push({
            name: productName,
            price: price,
            owner: owner,
            quantity: 1
        });
        showNotification('Added to cart successfully!');
    }
    
    // 保存到本地存储
    localStorage.setItem('selectedProducts', JSON.stringify(selectedProducts));
    
    // 刷新显示
    displayCart();
    loadProducts(); // 重新渲染产品卡片以更新按钮状态
}

function updateQuantity(productName, change) {
    const item = selectedProducts.find(item => item.name === productName);
    if (item) {
        item.quantity += change;
        if (item.quantity <= 0) {
            removeFromCart(productName);
        } else {
            localStorage.setItem('selectedProducts', JSON.stringify(selectedProducts));
            displayCart();
            loadProducts();
        }
    }
}

function removeFromCart(productName) {
    selectedProducts = selectedProducts.filter(item => item.name !== productName);
    localStorage.setItem('selectedProducts', JSON.stringify(selectedProducts));
    showNotification('Item removed from cart');
    displayCart();
    loadProducts();
}

function clearCart() {
    selectedProducts = [];
    localStorage.removeItem('selectedProducts');
    showNotification('Cart cleared');
    displayCart();
    loadProducts();
}

function displayCart() {
    const cartContainer = document.getElementById('cartItems');
    const submitBtn = document.getElementById('submitOrderBtn');
    
    if (selectedProducts.length === 0) {
        cartContainer.innerHTML = '<p style="text-align: center; color: var(--gray);">Your cart is empty</p>';
        submitBtn.style.display = 'none';
        return;
    }
    
    let total = 0;
    cartContainer.innerHTML = '';
    
    selectedProducts.forEach(item => {
        total += item.price * item.quantity;
        
        const cartItem = document.createElement('div');
        cartItem.className = 'cart-item';
        cartItem.innerHTML = `
            <div class="cart-item-info">
                <div class="cart-item-name">${item.name}</div>
                <div class="cart-item-price">$${item.price} each</div>
            </div>
            <div class="cart-item-quantity">
                <button class="quantity-btn" onclick="updateQuantity('${item.name}', -1)">-</button>
                <span class="quantity-display">${item.quantity}</span>
                <button class="quantity-btn" onclick="updateQuantity('${item.name}', 1)">+</button>
            </div>
        `;
        cartContainer.appendChild(cartItem);
    });
    
    // 添加总计
    const totalElement = document.createElement('div');
    totalElement.className = 'cart-total';
    totalElement.innerHTML = `Total: $${total.toFixed(2)}`;
    cartContainer.appendChild(totalElement);
    
    submitBtn.style.display = 'block';
}

async function submitOrder() {
    if (selectedProducts.length === 0) {
        showNotification('Cart is empty', 'error');
        return;
    }
    
    // 获取订单中的第一个商品作为机器人运输目标
    const targetProduct = selectedProducts[0].name;
    
    // 添加订单到订单历史（不直接发送给机器人）
    selectedProducts.forEach(item => {
        allOrders.push({
            customer: currentUser,
            product: item.name,
            quantity: item.quantity,
            date: new Date().toLocaleDateString(),
            vendor: item.owner,
            price: item.price,
            status: 'pending' // 添加状态字段
        });
    });
    
    // 保存订单到本地存储
    localStorage.setItem('allOrders', JSON.stringify(allOrders));
    
    showNotification(`订单已提交！等待商家处理: ${targetProduct}`);
    
    // 清空购物车
    selectedProducts = [];
    localStorage.removeItem('selectedProducts');
    
    displayCart();
    loadOrderHistory();
    loadProducts();
}

function loadOrderHistory() {
    // 从本地存储加载订单历史
    const savedOrders = localStorage.getItem('allOrders');
    if (savedOrders) {
        allOrders = JSON.parse(savedOrders);
    }
    
    displayOrderHistory();
}

function displayOrderHistory() {
    const list = document.getElementById('subscriptionsList');
    list.innerHTML = '';
    
    // 获取当前用户的订单
    const userOrders = allOrders.filter(order => order.customer === currentUser);
    
    if (userOrders.length === 0) {
        list.innerHTML = '<p style="text-align: center; color: var(--gray);">No order history</p>';
        return;
    }
    
    userOrders.reverse().forEach(order => {
        const item = document.createElement('div');
        item.className = 'subscription-item';
        item.innerHTML = `
            <div class="subscription-name">${order.product}</div>
            <div class="subscription-price">$${order.price} x ${order.quantity}</div>
            <div class="subscription-date">Ordered: ${order.date}</div>
        `;
        list.appendChild(item);
    });
}

// 商家功能
async function addProduct(event) {
    event.preventDefault();
    
    const name = document.getElementById('productName').value;
    const description = document.getElementById('productDescription').value;
    const category = document.getElementById('productCategory').value;
    const price = parseFloat(document.getElementById('productPrice').value);
    const stock = parseInt(document.getElementById('productStock').value);
    
    showLoading();
    
    try {
        const response = await sendRequest('AddProduct', {
            name: name,
            desc: description,
            category: category,
            price: price,
            stock: stock
        });
        
        if (response.ok) {
            hideAddProductModal();
            showNotification('Product added successfully!');
            document.getElementById('addProductForm').reset();
            loadProducts();
            loadSellerProducts();
        } else {
            showNotification('Failed to add product', 'error');
        }
    } catch (error) {
        showNotification('Server connection failed', 'error');
    } finally {
        hideLoading();
    }
}

async function loadSellerProducts() {
    // 获取当前商家的商品
    const sellerProducts = products.filter(product => product.owner === currentUser);
    displaySellerProducts(sellerProducts);
}

function displaySellerProducts(sellerProducts) {
    const container = document.getElementById('sellerProducts');
    container.innerHTML = '';
    
    if (sellerProducts.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--gray);">No products</p>';
        return;
    }
    
    sellerProducts.forEach(product => {
        const card = document.createElement('div');
        card.className = 'seller-product-card';
        card.innerHTML = `
            <div class="product-category">
                <i class="${getCategoryIcon(product.cat)}"></i> ${product.cat}
            </div>
            <div class="product-name">${product.name}</div>
            <div class="product-description">${product.desc}</div>
            <div class="product-price">$${product.price}</div>
            <div class="product-stock">Stock: ${product.stock}</div>
        `;
        container.appendChild(card);
    });
}

async function loadSubscriptionAnalytics() {
    // 使用本地订单数据进行分析
    const sellerProducts = products.filter(p => p.owner === currentUser);
    const sellerProductNames = sellerProducts.map(p => p.name);
    const sellerOrders = allOrders.filter(order => 
        sellerProductNames.includes(order.product)
    );
    
    // 计算总订阅数
    const totalSubscribers = sellerOrders.length;
    document.getElementById('totalSubscribers').textContent = totalSubscribers;
    
    // 找出最受欢迎的商品
    const productCounts = {};
    sellerOrders.forEach(order => {
        productCounts[order.product] = (productCounts[order.product] || 0) + order.quantity;
    });
    
    const popularProduct = Object.keys(productCounts).length > 0 ? 
        Object.keys(productCounts).reduce((a, b) => 
            productCounts[a] > productCounts[b] ? a : b
        ) : '-';
    document.getElementById('popularProduct').textContent = popularProduct;
    
    // 显示详细订阅信息
    displayDetailedSubscriptions(sellerOrders);
}

function refreshSubscriptionData() {
    // 从本地存储重新加载订单数据
    const savedOrders = localStorage.getItem('allOrders');
    if (savedOrders) {
        allOrders = JSON.parse(savedOrders);
    }
    
    // 重新加载分析数据
    loadSubscriptionAnalytics();
    showNotification('Data refreshed successfully!');
}

function displayDetailedSubscriptions(orders) {
    const container = document.getElementById('detailedSubscriptions');
    container.innerHTML = '';
    
    if (orders.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--gray);">No subscription data</p>';
        return;
    }
    
    // Add table header
    const header = document.createElement('div');
    header.className = 'subscription-row';
    header.style.fontWeight = 'bold';
    header.style.background = 'var(--primary-color)';
    header.style.color = 'var(--white)';
    header.innerHTML = `
        <div>Customer</div>
        <div>Product</div>
        <div>Quantity</div>
        <div>Status</div>
    `;
    container.appendChild(header);
    
    // Add data rows
    orders.forEach(order => {
        const row = document.createElement('div');
        row.className = 'subscription-row';
        row.innerHTML = `
            <div>${order.customer}</div>
            <div>${order.product}</div>
            <div>${order.quantity}</div>
            <div><span style="color: var(--accent-color); font-weight: 500;">Subscribed</span></div>
        `;
        container.appendChild(row);
    });
}

// 显示商品（游客模式）
function showProducts() {
    document.getElementById('heroSection').classList.add('hidden');
    document.getElementById('customerView').classList.remove('hidden');
    document.getElementById('sellerView').classList.add('hidden');
    loadProducts();
}

// 工具函数
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    const text = document.getElementById('notificationText');
    
    text.textContent = message;
    notification.classList.remove('hidden');
    
    // 根据类型设置样式
    if (type === 'error') {
        notification.style.background = 'var(--gradient-secondary)';
    } else {
        notification.style.background = 'var(--gradient-accent)';
    }
    
    // 3秒后自动隐藏
    setTimeout(() => {
        notification.classList.add('hidden');
    }, 3000);
}

function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

// 点击模态框外部关闭
document.addEventListener('click', function(event) {
    const modals = document.querySelectorAll('.modal-overlay');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.classList.add('hidden');
        }
    });
});

// ESC键关闭模态框
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modals = document.querySelectorAll('.modal-overlay');
        modals.forEach(modal => {
            modal.classList.add('hidden');
        });
    }
});

// ======== 设置面板功能 ========

// 更新设置显示
function updateSettingsDisplay() {
    // Update status information
    document.getElementById('connectionStatus').textContent = 'Local Mode';
    document.getElementById('productCount').textContent = mockProducts.length;
    document.getElementById('currentUserStatus').textContent = currentUser || 'Not logged in';
    
    // 根据本地存储恢复设置
    const enableAnimations = localStorage.getItem('enableAnimations') !== 'false';
    const enableNotifications = localStorage.getItem('enableNotifications') !== 'false';
    
    document.getElementById('enableAnimations').checked = enableAnimations;
    document.getElementById('enableNotifications').checked = enableNotifications;
}

// 切换连接模式
function changeConnectionMode() {
    const mode = document.querySelector('input[name="connectionMode"]:checked').value;
    localStorage.setItem('connectionMode', mode);
    
    if (mode === 'local') {
        showNotification('Switched to local mock mode');
        document.getElementById('connectionStatus').textContent = 'Local Mode';
    } else {
        showNotification('Switched to server connection mode');
        document.getElementById('connectionStatus').textContent = 'Server Mode';
    }
}

// 切换动画效果
function toggleAnimations() {
    const enabled = document.getElementById('enableAnimations').checked;
    localStorage.setItem('enableAnimations', enabled);
    
    if (enabled) {
        document.body.classList.remove('no-animations');
        showNotification('Animations enabled');
    } else {
        document.body.classList.add('no-animations');
        showNotification('Animations disabled');
    }
}

// 切换通知显示
function toggleNotifications() {
    const enabled = document.getElementById('enableNotifications').checked;
    localStorage.setItem('enableNotifications', enabled);
    
    if (enabled) {
        showNotification('Notifications enabled');
    } else {
        // Don't show notification since user just disabled notifications
        console.log('Notifications disabled');
    }
}

// 清除订单历史
function clearOrderHistory() {
    if (confirm('Are you sure you want to clear all order history? This action cannot be undone.')) {
        allOrders = [];
        localStorage.removeItem('allOrders');
        
        // 刷新相关显示
        if (userType === 'Customer') {
            displayOrderHistory();
        } else if (userType === 'Seller') {
            loadSubscriptionAnalytics();
        }
        
        showNotification('Order history cleared');
    }
}

function clearAllOrders() {
    if (confirm('Are you sure you want to clear all orders? This action cannot be undone.')) {
        allOrders = [];
        localStorage.removeItem('allOrders');
        loadPendingOrders();
        loadSubscriptionAnalytics();
        showNotification('All orders have been cleared!', 'success');
    }
}

// 清除本地数据
function clearLocalData() {
    if (confirm('Are you sure you want to clear all local data? This will delete your cart, order history, and settings.')) {
        localStorage.clear();
        selectedProducts = [];
        allOrders = [];
        
        // 重置界面
        showWelcomeView();
        if (userType === 'Customer') {
            displayCart();
            displayOrderHistory();
        }
        
        showNotification('All local data cleared');
    }
}

// 修改通知函数，检查设置
function showNotification(message, type = 'success') {
    const enableNotifications = localStorage.getItem('enableNotifications') !== 'false';
    if (!enableNotifications) return;
    
    const notification = document.getElementById('notification');
    const text = document.getElementById('notificationText');
    
    text.textContent = message;
    notification.classList.remove('hidden');
    
    // 根据类型设置样式
    if (type === 'error') {
        notification.style.background = 'var(--gradient-secondary)';
    } else {
        notification.style.background = 'var(--gradient-accent)';
    }
    
    // 3秒后自动隐藏
    setTimeout(() => {
        notification.classList.add('hidden');
    }, 3000);
}

// 页面加载时恢复设置
document.addEventListener('DOMContentLoaded', function() {
    // 恢复动画设置
    const enableAnimations = localStorage.getItem('enableAnimations') !== 'false';
    if (!enableAnimations) {
        document.body.classList.add('no-animations');
    }
    
    // 恢复连接模式设置
    const connectionMode = localStorage.getItem('connectionMode') || 'local';
    document.querySelector(`input[name="connectionMode"][value="${connectionMode}"]`).checked = true;
    
    console.log('🎉 System initialization complete');
    console.log('📊 Available demo accounts:');
    console.log('   Customers: customer1, customer2 (password: 123)');
    console.log('   Vendors: food_vendor, fruit_vendor, stationery_vendor (password: 123)');
    console.log('📦 Built-in products count:', mockProducts.length);
    console.log('⚙️  Click the settings button in the top right corner for more options');
    
    // 检查语音录制支持
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        console.log('🎤 Voice recording supported');
    } else {
        console.log('❌ Voice recording not supported');
        const voiceBtn = document.getElementById('voiceOrderBtn');
        if (voiceBtn) {
            voiceBtn.style.display = 'none';
        }
    }
}); 

// ======== 语音下单功能 ========

async function toggleVoiceOrder() {
    if (!currentUser || userType !== 'Customer') {
        showNotification('Please login with a customer account to use voice ordering', 'error');
        return;
    }

    if (isRecording) {
        stopRecording();
    } else {
        await startRecording();
    }
}

async function startRecording() {
    try {
        // 请求麦克风权限
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                sampleRate: 16000,
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true
            } 
        });

        // 初始化录音器
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: 'audio/webm;codecs=opus'
        });

        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = () => {
            stream.getTracks().forEach(track => track.stop());
            processVoiceOrder();
        };

        // 开始录制
        mediaRecorder.start();
        isRecording = true;

        // 更新UI
        const voiceBtn = document.getElementById('voiceOrderBtn');
        voiceBtn.classList.add('recording');
        voiceBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Recording';

        showNotification('🎤 Recording... Speak your order clearly');

        // 自动停止录制（最多10秒）
        setTimeout(() => {
            if (isRecording) {
                stopRecording();
            }
        }, 10000);

    } catch (error) {
        console.error('Error starting recording:', error);
        showNotification('Unable to access microphone. Please check permissions.', 'error');
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;

        // 更新UI
        const voiceBtn = document.getElementById('voiceOrderBtn');
        voiceBtn.classList.remove('recording');
        voiceBtn.classList.add('processing');
        voiceBtn.innerHTML = '<i class="fas fa-spinner"></i> Processing...';
    }
}

async function processVoiceOrder() {
    try {
        if (audioChunks.length === 0) {
            throw new Error('No audio data recorded');
        }

        // 创建音频文件
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        
        // 转换为WAV格式（更好的兼容性）
        const audioBuffer = await audioBlob.arrayBuffer();
        const audioFile = new Blob([audioBuffer], { type: 'audio/wav' });

        // 准备FormData
        const formData = new FormData();
        formData.append('audio', audioFile, 'voice_order.wav');

        // 发送到语音识别API
        console.log('🎤 Sending audio to voice recognition API...');
        const response = await fetch(VOICE_API_URL, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            console.log('✅ Voice recognition successful:', result);
            displayVoiceResult(result.transcribed_text, result.order);
            addVoiceOrderToCart(result.order);
        } else {
            throw new Error(result.error || 'Voice recognition failed');
        }

    } catch (error) {
        console.error('❌ Voice processing error:', error);
        
        // 检查是否是API连接错误
        if (error.message.includes('fetch')) {
            showNotification('Voice recognition service unavailable. Please start the Python API server.', 'error');
        } else {
            showNotification(`Voice recognition failed: ${error.message}`, 'error');
        }
        
        hideVoiceResult();
    } finally {
        // 重置UI
        const voiceBtn = document.getElementById('voiceOrderBtn');
        voiceBtn.classList.remove('processing', 'recording');
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i> Voice Order';
        
        // 清理音频数据
        audioChunks = [];
    }
}

function displayVoiceResult(transcribedText, order) {
    const resultDiv = document.getElementById('voiceResult');
    const textDiv = document.getElementById('voiceResultText');
    const orderDiv = document.getElementById('voiceResultOrder');

    textDiv.textContent = `🎤 You said: "${transcribedText}"`;
    orderDiv.textContent = `📦 Recognized order: ${order.quantity} x ${order.product}`;

    resultDiv.classList.add('show');

    // 5秒后自动隐藏
    setTimeout(() => {
        hideVoiceResult();
    }, 5000);
}

function hideVoiceResult() {
    const resultDiv = document.getElementById('voiceResult');
    resultDiv.classList.remove('show');
}

function addVoiceOrderToCart(order) {
    console.log('🔍 Processing voice order:', order);
    console.log('📦 Available products:', products.map(p => p.name));
    
    // 智能匹配商品名称
    let product = null;
    
    // 首先尝试精确匹配（不区分大小写）
    product = products.find(p => p.name.toLowerCase() === order.product.toLowerCase());
    
    // 如果没找到，尝试部分匹配（包含关键词）
    if (!product) {
        product = products.find(p => 
            order.product.toLowerCase().includes(p.name.toLowerCase()) ||
            p.name.toLowerCase().includes(order.product.toLowerCase())
        );
    }
    
    // 如果还没找到，尝试关键词匹配
    if (!product) {
        const keywords = {
            'banana': 'Banana',
            'bananas': 'Banana',
            'fresh': 'Banana',
            'book': 'Book',
            'books': 'Book'
        };
        
        for (const [keyword, productName] of Object.entries(keywords)) {
            if (order.product.toLowerCase().includes(keyword)) {
                product = products.find(p => p.name === productName);
                if (product) break;
            }
        }
    }
    
    if (!product) {
        console.log('❌ Product not found:', order.product);
        showNotification(`Product "${order.product}" not found in catalog. Available: ${products.map(p => p.name).join(', ')}`, 'error');
        return;
    }

    console.log('✅ Found product:', product);

    // 检查现有购物车中是否已有该商品
    const existingItem = selectedProducts.find(item => item.name === product.name);
    
    if (existingItem) {
        existingItem.quantity += order.quantity;
        showNotification(`Updated quantity: ${existingItem.quantity} x ${product.name}`);
    } else {
        selectedProducts.push({
            name: product.name, // 使用正确的商品名称（首字母大写）
            price: product.price,
            owner: product.owner,
            quantity: order.quantity
        });
        showNotification(`Added to cart: ${order.quantity} x ${product.name}`);
    }

    // 保存到本地存储
    localStorage.setItem('selectedProducts', JSON.stringify(selectedProducts));
    
    // 刷新显示
    displayCart();
    loadProducts(); // 重新渲染产品卡片以更新按钮状态
}

// 订单管理功能
function loadPendingOrders() {
    // 从本地存储加载订单数据
    const savedOrders = localStorage.getItem('allOrders');
    if (savedOrders) {
        allOrders = JSON.parse(savedOrders);
    }
    
    // 获取当前商家的待处理订单
    const sellerProducts = products.filter(p => p.owner === currentUser);
    const sellerProductNames = sellerProducts.map(p => p.name);
    const pendingOrders = allOrders.filter(order => 
        sellerProductNames.includes(order.product) && order.status === 'pending'
    );
    
    displayPendingOrders(pendingOrders);
}

function displayPendingOrders(orders) {
    const container = document.getElementById('pendingOrders');
    container.innerHTML = '';
    
    if (orders.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--gray);">No pending orders</p>';
        return;
    }
    
    // Add table header
    const header = document.createElement('div');
    header.className = 'order-row';
    header.style.fontWeight = 'bold';
    header.style.background = 'var(--primary-color)';
    header.style.color = 'var(--white)';
    header.innerHTML = `
        <div>Customer</div>
        <div>Product</div>
        <div>Quantity</div>
        <div>Date</div>
        <div>Status</div>
    `;
    container.appendChild(header);
    
    // Add data rows
    orders.forEach(order => {
        const row = document.createElement('div');
        row.className = 'order-row';
        row.innerHTML = `
            <div>${order.customer}</div>
            <div>${order.product}</div>
            <div>${order.quantity}</div>
            <div>${order.date}</div>
            <div><span style="color: var(--accent-color); font-weight: 500;">Pending</span></div>
        `;
        container.appendChild(row);
    });
}

async function sendPendingOrdersToRobot() {
    // 获取当前商家的待处理订单
    const sellerProducts = products.filter(p => p.owner === currentUser);
    const sellerProductNames = sellerProducts.map(p => p.name);
    const pendingOrders = allOrders.filter(order => 
        sellerProductNames.includes(order.product) && order.status === 'pending'
    );
    
    if (pendingOrders.length === 0) {
        showNotification('No pending orders to send', 'warning');
        return;
    }
    
    // 获取第一个待处理订单的商品和客户信息
    const targetProduct = pendingOrders[0].product;
    const targetCustomer = pendingOrders[0].customer; // 使用实际下单的客户
    
    try {
        const response = await fetch('http://localhost:5001/set_order_target', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                product: targetProduct,
                customer: targetCustomer
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.status === 'success') {
                // 更新订单状态为已发送
                pendingOrders[0].status = 'sent';
                localStorage.setItem('allOrders', JSON.stringify(allOrders));
                
                showNotification(`订单已发送给机器人: ${targetProduct}`);
                loadPendingOrders(); // 刷新显示
            } else if (data.status === 'warning') {
                showNotification('订单发送失败，但已记录', 'warning');
            } else {
                showNotification(`发送失败: ${data.message}`, 'error');
            }
        } else {
            const errorData = await response.json();
            showNotification(`发送失败: ${errorData.message}`, 'error');
        }
    } catch (error) {
        console.error('MQTT服务连接失败:', error);
        showNotification('MQTT服务连接失败', 'error');
    }
}

function refreshOrderData() {
    loadPendingOrders();
    loadSubscriptionAnalytics();
    showNotification('Order data refreshed successfully!');
}