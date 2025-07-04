/**
 * Alfamart Stock Management System - Frontend Application
 * Implements MVC pattern with proper separation of concerns
 */

// Application State Management
class AppState {
    constructor() {
        this.categories = [];
        this.suppliers = [];
        this.products = [];
        this.transactions = [];
        this.currentSection = 'dashboard';
        this.editingItem = null;
    }

    updateCategories(categories) {
        this.categories = categories;
    }

    updateSuppliers(suppliers) {
        this.suppliers = suppliers;
    }

    updateProducts(products) {
        this.products = products;
    }

    updateTransactions(transactions) {
        this.transactions = transactions;
    }
}

// API Service Layer
class ApiService {
    constructor() {
        this.baseUrl = '/api';
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            showLoading();
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            showToast(error.message, 'error');
            throw error;
        } finally {
            hideLoading();
        }
    }

    // Category API methods
    async getCategories() {
        return this.request('/categories');
    }

    async createCategory(categoryData) {
        return this.request('/categories', {
            method: 'POST',
            body: JSON.stringify(categoryData)
        });
    }

    async updateCategory(id, categoryData) {
        return this.request(`/categories/${id}`, {
            method: 'PUT',
            body: JSON.stringify(categoryData)
        });
    }

    async deleteCategory(id) {
        return this.request(`/categories/${id}`, {
            method: 'DELETE'
        });
    }

    // Supplier API methods
    async getSuppliers() {
        return this.request('/suppliers');
    }

    async createSupplier(supplierData) {
        return this.request('/suppliers', {
            method: 'POST',
            body: JSON.stringify(supplierData)
        });
    }

    async updateSupplier(id, supplierData) {
        return this.request(`/suppliers/${id}`, {
            method: 'PUT',
            body: JSON.stringify(supplierData)
        });
    }

    async deleteSupplier(id) {
        return this.request(`/suppliers/${id}`, {
            method: 'DELETE'
        });
    }

    // Product API methods
    async getProducts(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/products?${params}`);
    }

    async createProduct(productData) {
        return this.request('/products', {
            method: 'POST',
            body: JSON.stringify(productData)
        });
    }

    async updateProduct(id, productData) {
        return this.request(`/products/${id}`, {
            method: 'PUT',
            body: JSON.stringify(productData)
        });
    }

    async deleteProduct(id) {
        return this.request(`/products/${id}`, {
            method: 'DELETE'
        });
    }

    async getLowStockProducts() {
        return this.request('/products/low-stock');
    }

    // Transaction API methods
    async getTransactions(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/stock-transactions?${params}`);
    }

    async createTransaction(transactionData) {
        return this.request('/stock-transactions', {
            method: 'POST',
            body: JSON.stringify(transactionData)
        });
    }

    async processTransaction(id) {
        return this.request(`/stock-transactions/${id}/process`, {
            method: 'POST'
        });
    }
}

// UI Controller
class UIController {
    constructor(apiService, appState) {
        this.api = apiService;
        this.state = appState;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchSection(e.target.dataset.section);
            });
        });

        // Form submissions
        document.getElementById('category-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleCategorySubmit();
        });

        document.getElementById('supplier-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSupplierSubmit();
        });

        document.getElementById('product-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleProductSubmit();
        });

        document.getElementById('transaction-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleTransactionSubmit();
        });

        // Search and filters
        document.getElementById('product-search').addEventListener('input', 
            debounce(() => this.loadProducts(), 300));

        document.getElementById('category-filter').addEventListener('change', () => this.loadProducts());
        document.getElementById('supplier-filter').addEventListener('change', () => this.loadProducts());
        document.getElementById('stock-status-filter').addEventListener('change', () => this.loadProducts());

        // Modal close on outside click
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeAllModals();
            }
        });
    }

    switchSection(sectionName) {
        // Update navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');

        // Update sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(sectionName).classList.add('active');

        this.state.currentSection = sectionName;

        // Load section data
        this.loadSectionData(sectionName);
    }

    async loadSectionData(sectionName) {
        switch (sectionName) {
            case 'dashboard':
                await this.loadDashboard();
                break;
            case 'categories':
                await this.loadCategories();
                break;
            case 'suppliers':
                await this.loadSuppliers();
                break;
            case 'products':
                await this.loadProducts();
                await this.loadProductFilters();
                break;
            case 'transactions':
                await this.loadTransactions();
                break;
        }
    }

    async loadDashboard() {
        try {
            const [categoriesRes, suppliersRes, productsRes, lowStockRes, transactionsRes] = await Promise.all([
                this.api.getCategories(),
                this.api.getSuppliers(),
                this.api.getProducts(),
                this.api.getLowStockProducts(),
                this.api.getTransactions({ per_page: 5 })
            ]);

            // Update stats
            document.getElementById('total-categories').textContent = categoriesRes.count;
            document.getElementById('total-suppliers').textContent = suppliersRes.count;
            document.getElementById('total-products').textContent = productsRes.count;
            document.getElementById('low-stock-count').textContent = lowStockRes.count;

            // Update low stock products
            this.renderLowStockProducts(lowStockRes.data);

            // Update recent transactions
            this.renderRecentTransactions(transactionsRes.data);

        } catch (error) {
            console.error('Error loading dashboard:', error);
        }
    }

    renderLowStockProducts(products) {
        const container = document.getElementById('low-stock-products');
        
        if (products.length === 0) {
            container.innerHTML = '<p>No low stock products</p>';
            return;
        }

        container.innerHTML = products.map(product => `
            <div class="product-item">
                <div class="product-info">
                    <h4>${product.name} (${product.code})</h4>
                    <p>Stock: ${product.stock_quantity} | Min: ${product.minimum_stock}</p>
                </div>
                <span class="status-badge status-${product.stock_status.toLowerCase().replace('_', '-')}">
                    ${product.stock_status.replace('_', ' ')}
                </span>
            </div>
        `).join('');
    }

    renderRecentTransactions(transactions) {
        const container = document.getElementById('recent-transactions');
        
        if (transactions.length === 0) {
            container.innerHTML = '<p>No recent transactions</p>';
            return;
        }

        container.innerHTML = transactions.map(transaction => `
            <div class="transaction-item">
                <div class="transaction-info">
                    <h4>${transaction.reference_number}</h4>
                    <p>${transaction.transaction_type} | Qty: ${transaction.quantity}</p>
                </div>
                <span class="status-badge status-${transaction.is_processed ? 'processed' : 'pending'}">
                    ${transaction.is_processed ? 'Processed' : 'Pending'}
                </span>
            </div>
        `).join('');
    }

    async loadCategories() {
        try {
            const response = await this.api.getCategories();
            this.state.updateCategories(response.data);
            this.renderCategoriesTable(response.data);
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }

    renderCategoriesTable(categories) {
        const tbody = document.querySelector('#categories-table tbody');
        
        if (categories.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No categories found</td></tr>';
            return;
        }

        tbody.innerHTML = categories.map(category => `
            <tr>
                <td>${category.code}</td>
                <td>${category.name}</td>
                <td>${category.description || '-'}</td>
                <td>${category.product_count}</td>
                <td>
                    <span class="status-badge status-${category.is_active ? 'active' : 'inactive'}">
                        ${category.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-warning" onclick="editCategory(${category.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteCategory(${category.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    async loadSuppliers() {
        try {
            const response = await this.api.getSuppliers();
            this.state.updateSuppliers(response.data);
            this.renderSuppliersTable(response.data);
        } catch (error) {
            console.error('Error loading suppliers:', error);
        }
    }

    renderSuppliersTable(suppliers) {
        const tbody = document.querySelector('#suppliers-table tbody');
        
        if (suppliers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">No suppliers found</td></tr>';
            return;
        }

        tbody.innerHTML = suppliers.map(supplier => `
            <tr>
                <td>${supplier.code}</td>
                <td>${supplier.name}</td>
                <td>
                    ${supplier.contact_info.phone || '-'}<br>
                    ${supplier.contact_info.email || '-'}
                </td>
                <td>$${supplier.credit_limit.toFixed(2)}</td>
                <td>${supplier.payment_terms} days</td>
                <td>
                    <span class="status-badge status-${supplier.is_active ? 'active' : 'inactive'}">
                        ${supplier.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-warning" onclick="editSupplier(${supplier.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteSupplier(${supplier.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    async loadProducts() {
        try {
            const filters = this.getProductFilters();
            const response = await this.api.getProducts(filters);
            this.state.updateProducts(response.data);
            this.renderProductsTable(response.data);
        } catch (error) {
            console.error('Error loading products:', error);
        }
    }

    getProductFilters() {
        const filters = {};
        
        const search = document.getElementById('product-search').value;
        if (search) filters.search_name = search;
        
        const categoryId = document.getElementById('category-filter').value;
        if (categoryId) filters.category_id = categoryId;
        
        const supplierId = document.getElementById('supplier-filter').value;
        if (supplierId) filters.supplier_id = supplierId;
        
        const stockStatus = document.getElementById('stock-status-filter').value;
        if (stockStatus) filters.stock_status = stockStatus;
        
        return filters;
    }

    async loadProductFilters() {
        // Load categories for filter
        const categorySelect = document.getElementById('category-filter');
        categorySelect.innerHTML = '<option value="">All Categories</option>';
        this.state.categories.forEach(category => {
            categorySelect.innerHTML += `<option value="${category.id}">${category.name}</option>`;
        });

        // Load suppliers for filter
        const supplierSelect = document.getElementById('supplier-filter');
        supplierSelect.innerHTML = '<option value="">All Suppliers</option>';
        this.state.suppliers.forEach(supplier => {
            supplierSelect.innerHTML += `<option value="${supplier.id}">${supplier.name}</option>`;
        });
    }

    renderProductsTable(products) {
        const tbody = document.querySelector('#products-table tbody');
        
        if (products.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center">No products found</td></tr>';
            return;
        }

        tbody.innerHTML = products.map(product => {
            const category = this.state.categories.find(c => c.id === product.category_id);
            const supplier = this.state.suppliers.find(s => s.id === product.supplier_id);
            
            return `
                <tr>
                    <td>${product.code}</td>
                    <td>${product.name}</td>
                    <td>${category ? category.name : '-'}</td>
                    <td>${supplier ? supplier.name : '-'}</td>
                    <td>
                        <span class="status-badge status-${product.stock_status.toLowerCase().replace('_', '-')}">
                            ${product.stock_quantity}
                        </span>
                    </td>
                    <td>$${product.unit_price.toFixed(2)}</td>
                    <td>
                        <span class="status-badge status-${product.is_active ? 'active' : 'inactive'}">
                            ${product.is_active ? 'Active' : 'Inactive'}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-warning" onclick="editProduct(${product.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteProduct(${product.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    async loadTransactions() {
        try {
            const filters = this.getTransactionFilters();
            const response = await this.api.getTransactions(filters);
            this.state.updateTransactions(response.data);
            this.renderTransactionsTable(response.data);
        } catch (error) {
            console.error('Error loading transactions:', error);
        }
    }

    getTransactionFilters() {
        const filters = {};
        
        const transactionType = document.getElementById('transaction-type-filter').value;
        if (transactionType) filters.transaction_type = transactionType;
        
        const startDate = document.getElementById('start-date-filter').value;
        if (startDate) filters.start_date = startDate;
        
        const endDate = document.getElementById('end-date-filter').value;
        if (endDate) filters.end_date = endDate;
        
        return filters;
    }

    renderTransactionsTable(transactions) {
        const tbody = document.querySelector('#transactions-table tbody');
        
        if (transactions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center">No transactions found</td></tr>';
            return;
        }

        tbody.innerHTML = transactions.map(transaction => {
            const product = this.state.products.find(p => p.id === transaction.product_id);
            
            return `
                <tr>
                    <td>${transaction.reference_number}</td>
                    <td>${transaction.transaction_type}</td>
                    <td>${product ? product.name : '-'}</td>
                    <td>${transaction.quantity}</td>
                    <td>$${transaction.unit_cost ? transaction.unit_cost.toFixed(2) : '-'}</td>
                    <td>$${transaction.total_cost.toFixed(2)}</td>
                    <td>
                        <span class="status-badge status-${transaction.is_processed ? 'processed' : 'pending'}">
                            ${transaction.is_processed ? 'Processed' : 'Pending'}
                        </span>
                    </td>
                    <td>${new Date(transaction.created_at).toLocaleDateString()}</td>
                    <td>
                        ${!transaction.is_processed ? `
                            <button class="btn btn-sm btn-success" onclick="processTransaction(${transaction.id})">
                                <i class="fas fa-check"></i>
                            </button>
                        ` : ''}
                    </td>
                </tr>
            `;
        }).join('');
    }

    // Form handlers
    async handleCategorySubmit() {
        try {
            const formData = this.getCategoryFormData();
            
            if (this.state.editingItem) {
                await this.api.updateCategory(this.state.editingItem.id, formData);
                showToast('Category updated successfully');
            } else {
                await this.api.createCategory(formData);
                showToast('Category created successfully');
            }
            
            this.closeCategoryModal();
            await this.loadCategories();
        } catch (error) {
            console.error('Error saving category:', error);
        }
    }

    getCategoryFormData() {
        return {
            name: document.getElementById('category-name').value,
            code: document.getElementById('category-code').value,
            description: document.getElementById('category-description').value
        };
    }

    async handleSupplierSubmit() {
        try {
            const formData = this.getSupplierFormData();
            
            if (this.state.editingItem) {
                await this.api.updateSupplier(this.state.editingItem.id, formData);
                showToast('Supplier updated successfully');
            } else {
                await this.api.createSupplier(formData);
                showToast('Supplier created successfully');
            }
            
            this.closeSupplierModal();
            await this.loadSuppliers();
        } catch (error) {
            console.error('Error saving supplier:', error);
        }
    }

    getSupplierFormData() {
        return {
            name: document.getElementById('supplier-name').value,
            code: document.getElementById('supplier-code').value,
            contact_info: {
                phone: document.getElementById('supplier-phone').value,
                email: document.getElementById('supplier-email').value,
                address: document.getElementById('supplier-address').value
            },
            credit_limit: parseFloat(document.getElementById('supplier-credit-limit').value) || 0,
            payment_terms: parseInt(document.getElementById('supplier-payment-terms').value) || 30
        };
    }

    async handleProductSubmit() {
        try {
            const formData = this.getProductFormData();
            
            if (this.state.editingItem) {
                await this.api.updateProduct(this.state.editingItem.id, formData);
                showToast('Product updated successfully');
            } else {
                await this.api.createProduct(formData);
                showToast('Product created successfully');
            }
            
            this.closeProductModal();
            await this.loadProducts();
        } catch (error) {
            console.error('Error saving product:', error);
        }
    }

    getProductFormData() {
        const formData = {
            name: document.getElementById('product-name').value,
            code: document.getElementById('product-code').value,
            barcode: document.getElementById('product-barcode').value,
            description: document.getElementById('product-description').value,
            category_id: parseInt(document.getElementById('product-category').value),
            supplier_id: parseInt(document.getElementById('product-supplier').value),
            cost_price: parseFloat(document.getElementById('product-cost-price').value),
            unit_price: parseFloat(document.getElementById('product-unit-price').value),
            minimum_stock: parseInt(document.getElementById('product-minimum-stock').value) || 0,
            maximum_stock: parseInt(document.getElementById('product-maximum-stock').value) || 1000,
            unit_of_measure: document.getElementById('product-unit-measure').value
        };

        const expiryDate = document.getElementById('product-expiry-date').value;
        if (expiryDate) {
            formData.expiry_date = expiryDate;
        }

        return formData;
    }

    async handleTransactionSubmit() {
        try {
            const formData = this.getTransactionFormData();
            
            await this.api.createTransaction(formData);
            showToast('Transaction created successfully');
            
            this.closeTransactionModal();
            await this.loadTransactions();
            
            // Refresh products if we're on that section
            if (this.state.currentSection === 'products') {
                await this.loadProducts();
            }
        } catch (error) {
            console.error('Error saving transaction:', error);
        }
    }

    getTransactionFormData() {
        const formData = {
            transaction_type: document.getElementById('transaction-type').value,
            reference_number: document.getElementById('transaction-reference').value,
            product_id: parseInt(document.getElementById('transaction-product').value),
            quantity: parseInt(document.getElementById('transaction-quantity').value),
            notes: document.getElementById('transaction-notes').value,
            processed_by: document.getElementById('transaction-processed-by').value,
            auto_process: document.getElementById('auto-process').checked
        };

        const unitCost = document.getElementById('transaction-unit-cost').value;
        if (unitCost) {
            formData.unit_cost = parseFloat(unitCost);
        }

        return formData;
    }

    // Modal management
    closeCategoryModal() {
        document.getElementById('category-modal').style.display = 'none';
        document.getElementById('category-form').reset();
        this.state.editingItem = null;
    }

    closeSupplierModal() {
        document.getElementById('supplier-modal').style.display = 'none';
        document.getElementById('supplier-form').reset();
        this.state.editingItem = null;
    }

    closeProductModal() {
        document.getElementById('product-modal').style.display = 'none';
        document.getElementById('product-form').reset();
        this.state.editingItem = null;
    }

    closeTransactionModal() {
        document.getElementById('transaction-modal').style.display = 'none';
        document.getElementById('transaction-form').reset();
        this.state.editingItem = null;
    }

    closeAllModals() {
        this.closeCategoryModal();
        this.closeSupplierModal();
        this.closeProductModal();
        this.closeTransactionModal();
    }

    async populateProductSelects() {
        // Populate category select
        const categorySelect = document.getElementById('product-category');
        categorySelect.innerHTML = '<option value="">Select Category</option>';
        this.state.categories.forEach(category => {
            categorySelect.innerHTML += `<option value="${category.id}">${category.name}</option>`;
        });

        // Populate supplier select
        const supplierSelect = document.getElementById('product-supplier');
        supplierSelect.innerHTML = '<option value="">Select Supplier</option>';
        this.state.suppliers.forEach(supplier => {
            supplierSelect.innerHTML += `<option value="${supplier.id}">${supplier.name}</option>`;
        });
    }

    async populateTransactionProductSelect() {
        const productSelect = document.getElementById('transaction-product');
        productSelect.innerHTML = '<option value="">Select Product</option>';
        this.state.products.forEach(product => {
            productSelect.innerHTML += `<option value="${product.id}">${product.name} (${product.code})</option>`;
        });
    }
}

// Global variables
let apiService;
let appState;
let uiController;

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function showLoading() {
    document.getElementById('loading').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    document.getElementById('toast-container').appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Global functions for button clicks
function showCategoryModal() {
    document.getElementById('category-modal-title').textContent = 'Add Category';
    document.getElementById('category-modal').style.display = 'block';
}

function showSupplierModal() {
    document.getElementById('supplier-modal-title').textContent = 'Add Supplier';
    document.getElementById('supplier-modal').style.display = 'block';
}

async function showProductModal() {
    document.getElementById('product-modal-title').textContent = 'Add Product';
    await uiController.populateProductSelects();
    document.getElementById('product-modal').style.display = 'block';
}

async function showTransactionModal() {
    document.getElementById('transaction-modal-title').textContent = 'New Transaction';
    await uiController.populateTransactionProductSelect();
    document.getElementById('transaction-modal').style.display = 'block';
}

function closeCategoryModal() {
    uiController.closeCategoryModal();
}

function closeSupplierModal() {
    uiController.closeSupplierModal();
}

function closeProductModal() {
    uiController.closeProductModal();
}

function closeTransactionModal() {
    uiController.closeTransactionModal();
}

function toggleTransactionFields() {
    const transactionType = document.getElementById('transaction-type').value;
    const unitCostGroup = document.getElementById('unit-cost-group');
    const unitCostInput = document.getElementById('transaction-unit-cost');
    
    if (transactionType === 'STOCK_IN') {
        unitCostGroup.style.display = 'block';
        unitCostInput.required = true;
    } else {
        unitCostGroup.style.display = 'none';
        unitCostInput.required = false;
    }
}

async function editCategory(id) {
    const category = appState.categories.find(c => c.id === id);
    if (category) {
        appState.editingItem = category;
        document.getElementById('category-modal-title').textContent = 'Edit Category';
        document.getElementById('category-name').value = category.name;
        document.getElementById('category-code').value = category.code;
        document.getElementById('category-description').value = category.description || '';
        document.getElementById('category-modal').style.display = 'block';
    }
}

async function deleteCategory(id) {
    if (confirm('Are you sure you want to delete this category?')) {
        try {
            await apiService.deleteCategory(id);
            showToast('Category deleted successfully');
            await uiController.loadCategories();
        } catch (error) {
            console.error('Error deleting category:', error);
        }
    }
}

async function editSupplier(id) {
    const supplier = appState.suppliers.find(s => s.id === id);
    if (supplier) {
        appState.editingItem = supplier;
        document.getElementById('supplier-modal-title').textContent = 'Edit Supplier';
        document.getElementById('supplier-name').value = supplier.name;
        document.getElementById('supplier-code').value = supplier.code;
        document.getElementById('supplier-phone').value = supplier.contact_info.phone || '';
        document.getElementById('supplier-email').value = supplier.contact_info.email || '';
        document.getElementById('supplier-address').value = supplier.contact_info.address || '';
        document.getElementById('supplier-credit-limit').value = supplier.credit_limit;
        document.getElementById('supplier-payment-terms').value = supplier.payment_terms;
        document.getElementById('supplier-modal').style.display = 'block';
    }
}

async function deleteSupplier(id) {
    if (confirm('Are you sure you want to delete this supplier?')) {
        try {
            await apiService.deleteSupplier(id);
            showToast('Supplier deleted successfully');
            await uiController.loadSuppliers();
        } catch (error) {
            console.error('Error deleting supplier:', error);
        }
    }
}

async function editProduct(id) {
    const product = appState.products.find(p => p.id === id);
    if (product) {
        appState.editingItem = product;
        document.getElementById('product-modal-title').textContent = 'Edit Product';
        await uiController.populateProductSelects();
        
        document.getElementById('product-name').value = product.name;
        document.getElementById('product-code').value = product.code;
        document.getElementById('product-barcode').value = product.barcode || '';
        document.getElementById('product-description').value = product.description || '';
        document.getElementById('product-category').value = product.category_id;
        document.getElementById('product-supplier').value = product.supplier_id;
        document.getElementById('product-cost-price').value = product.cost_price;
        document.getElementById('product-unit-price').value = product.unit_price;
        document.getElementById('product-minimum-stock').value = product.minimum_stock;
        document.getElementById('product-maximum-stock').value = product.maximum_stock;
        document.getElementById('product-unit-measure').value = product.unit_of_measure;
        document.getElementById('product-expiry-date').value = product.expiry_date || '';
        
        document.getElementById('product-modal').style.display = 'block';
    }
}

async function deleteProduct(id) {
    if (confirm('Are you sure you want to delete this product?')) {
        try {
            await apiService.deleteProduct(id);
            showToast('Product deleted successfully');
            await uiController.loadProducts();
        } catch (error) {
            console.error('Error deleting product:', error);
        }
    }
}

async function processTransaction(id) {
    if (confirm('Are you sure you want to process this transaction?')) {
        try {
            await apiService.processTransaction(id);
            showToast('Transaction processed successfully');
            await uiController.loadTransactions();
            
            // Refresh products if we're on that section
            if (appState.currentSection === 'products') {
                await uiController.loadProducts();
            }
        } catch (error) {
            console.error('Error processing transaction:', error);
        }
    }
}

async function loadTransactions() {
    await uiController.loadTransactions();
}

// Initialize application
document.addEventListener('DOMContentLoaded', async () => {
    apiService = new ApiService();
    appState = new AppState();
    uiController = new UIController(apiService, appState);
    
    // Load initial data
    await uiController.loadSectionData('dashboard');
    await uiController.loadCategories();
    await uiController.loadSuppliers();
});

