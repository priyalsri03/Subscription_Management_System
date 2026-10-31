/**
 * SaaS Subscription Management Dashboard - Frontend Application
 * Connects to FastAPI backend endpoints for Person 2 modules
 */

class SubscriptionDashboard {
    constructor() {
        this.apiBase = '/api/v1';
        this.currentPage = 'overview';
        this.customers = [];
        this.plans = [];
        this.products = [];
        this.state = {
            quotations: [],
            subscriptions: [],
            invoices: [],
            payments: []
        };
        this.init();
    }

    async init() {
        this.bindEvents();

        // Listen for browser back/forward (hashchange)
        window.addEventListener('hashchange', () => {
            const hash = window.location.hash.replace('#/', '');
            if (['quotations', 'subscriptions', 'invoices', 'payments'].includes(hash)) {
                // Navigate programmatically without re-binding events
                document.querySelectorAll('.page-section').forEach(section => {
                    section.classList.remove('active');
                });
                document.getElementById(`${hash}-page`)?.classList.add('active');

                const titles = {
                    overview: 'Dashboard',
                    quotations: 'Quotation Management',
                    subscriptions: 'Subscription Management',
                    invoices: 'Invoice Management',
                    payments: 'Payment Management'
                };
                document.getElementById('page-title').textContent = titles[hash] || 'Dashboard';

                document.querySelectorAll('.nav-link').forEach(link => {
                    link.classList.remove('active');
                });
                document.querySelector(`[data-page="${hash}"]`)?.classList.add('active');

                this.loadPageData(hash);
            }
        });

        // Check URL hash for remembered page
        const hash = window.location.hash.replace('#/', '');
        if (['quotations', 'subscriptions', 'invoices', 'payments'].includes(hash)) {
            this.currentPage = hash;
            // Show the remembered page without triggering navigateTo
            document.querySelectorAll('.page-section').forEach(section => {
                section.classList.remove('active');
            });
            document.getElementById(`${hash}-page`)?.classList.add('active');

            // Update page title
            const titles = {
                overview: 'Dashboard',
                quotations: 'Quotation Management',
                subscriptions: 'Subscription Management',
                invoices: 'Invoice Management',
                payments: 'Payment Management'
            };
            document.getElementById('page-title').textContent = titles[hash] || 'Dashboard';

            // Update nav link active state
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
            });
            document.querySelector(`[data-page="${hash}"]`)?.classList.add('active');

            // Load page-specific data
            await this.loadPageData(hash);
        } else {
            // Default: load overview
            this.loadOverviewData();
        }

        this.loadReferenceData();
    }

    bindEvents() {
        // Sidebar navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.dataset.page;
                this.navigateTo(page);
            });
        });

        // Refresh button
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.refreshCurrentPage();
        });

        // Modals
        this.setupModalEvents();

        // Form submissions
        document.getElementById('create-quotation-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.createQuotation();
        });

        document.getElementById('create-subscription-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.createSubscription();
        });

        document.getElementById('create-invoice-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.createInvoice();
        });

        document.getElementById('create-payment-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.createPayment();
        });
    }

    setupModalEvents() {
        // Quotation modal
        const quotationModal = document.getElementById('quotation-modal');
        quotationModal?.querySelector('.modal-close').addEventListener('click', () => {
            this.closeModal('quotation-modal');
        });
        document.getElementById('create-quotation-btn')?.addEventListener('click', () => {
            this.openQuotationModal();
        });
        document.querySelector('#quotation-modal .modal-cancel')?.addEventListener('click', () => {
            this.closeModal('quotation-modal');
        });
        document.getElementById('save-quotation-btn')?.addEventListener('click', () => {
            this.createQuotation();
        });

        // Subscription modal
        const subModal = document.getElementById('subscription-modal');
        subModal?.querySelector('.modal-close').addEventListener('click', () => {
            this.closeModal('subscription-modal');
        });
        document.getElementById('create-subscription-btn')?.addEventListener('click', () => {
            this.openSubscriptionModal();
        });
        document.querySelector('#subscription-modal .modal-cancel')?.addEventListener('click', () => {
            this.closeModal('subscription-modal');
        });
        document.getElementById('save-subscription-btn')?.addEventListener('click', () => {
            this.createSubscription();
        });

        // Subscription detail modal
        document.getElementById('subscription-detail-modal')?.querySelector('.modal-close')?.addEventListener('click', () => {
            this.closeModal('subscription-detail-modal');
        });

        // Invoice modal
        const invoiceModal = document.getElementById('invoice-modal');
        invoiceModal?.querySelector('.modal-close').addEventListener('click', () => {
            this.closeModal('invoice-modal');
        });
        document.getElementById('create-invoice-btn')?.addEventListener('click', () => {
            this.openInvoiceModal();
        });
        document.querySelector('#invoice-modal .modal-cancel')?.addEventListener('click', () => {
            this.closeModal('invoice-modal');
        });
        document.getElementById('save-invoice-btn')?.addEventListener('click', () => {
            this.createInvoice();
        });

        // Invoice detail modal
        document.getElementById('invoice-detail-modal')?.querySelector('.modal-close')?.addEventListener('click', () => {
            this.closeModal('invoice-detail-modal');
        });

        // Payment modal
        const paymentModal = document.getElementById('payment-modal');
        paymentModal?.querySelector('.modal-close').addEventListener('click', () => {
            this.closeModal('payment-modal');
        });
        document.getElementById('create-payment-btn')?.addEventListener('click', () => {
            this.openPaymentModal();
        });
        document.querySelector('#payment-modal .modal-cancel')?.addEventListener('click', () => {
            this.closeModal('payment-modal');
        });
        document.getElementById('save-payment-btn')?.addEventListener('click', () => {
            this.createPayment();
        });
    }

    navigateTo(page) {
        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        // Set active class on the link matching the page (more reliable than event.target)
        document.querySelector(`[data-page="${page}"]`)?.classList.add('active');

        // Show/hide pages
        document.querySelectorAll('.page-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(`${page}-page`)?.classList.add('active');

        // Update page title
        const titles = {
            overview: 'Dashboard',
            quotations: 'Quotation Management',
            subscriptions: 'Subscription Management',
            invoices: 'Invoice Management',
            payments: 'Payment Management'
        };
        document.getElementById('page-title').textContent = titles[page] || 'Dashboard';

        // Update URL hash for page persistence (only for non-overview pages)
        if (page !== 'overview') {
            window.location.hash = `#/${page}`;
        } else {
            window.location.hash = '';
        }

        // Load page-specific data
        this.loadPageData(page);
    }

    async loadPageData(page) {
        this.currentPage = page;
        switch (page) {
            case 'quotations':
                await this.loadQuotations();
                break;
            case 'subscriptions':
                await this.loadSubscriptions();
                break;
            case 'invoices':
                await this.loadInvoices();
                break;
            case 'payments':
                await this.loadPayments();
                break;
        }
    }

    refreshCurrentPage() {
        this.loadOverviewData();
        this.loadPageData(this.currentPage);
    }

    // API Helper Methods
    async apiGet(endpoint) {
        const response = await fetch(`${this.apiBase}${endpoint}`);
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        return response.json();
    }

    async apiPost(endpoint, data) {
        const response = await fetch(`${this.apiBase}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'API Error');
        }
        return response.json();
    }

    async apiDelete(endpoint) {
        const response = await fetch(`${this.apiBase}${endpoint}`, {
            method: 'DELETE'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'API Error');
        }
        return true;
    }

    async apiPatch(endpoint, data) {
        const response = await fetch(`${this.apiBase}${endpoint}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'API Error');
        }
        return response.json();
    }

    // Overview Dashboard
    async loadOverviewData() {
        try {
            const [subs, invoices, payments] = await Promise.all([
                this.apiGet('/subscriptions'),
                this.apiGet('/invoices'),
                this.apiGet('/payments')
            ]);

            this.state.subscriptions = subs;
            this.state.invoices = invoices;
            this.state.payments = payments;

            // Calculate stats
            const totalSubs = subs.length;
            const activeSubs = subs.filter(s => s.status === 'active' && !s.is_paused).length;
            const totalInvoices = invoices.length;
            const paidInvoices = invoices.filter(i => i.status === 'paid');
            const pendingInvoices = invoices.filter(i => i.status !== 'paid' && i.status !== 'cancelled');
            const overdueInvoices = invoices.filter(i => {
                const dueDate = new Date(i.due_date);
                const today = new Date();
                return i.status === 'confirmed' && dueDate < today && parseFloat(i.amount_paid) < parseFloat(i.total);
            });
            const totalRevenue = invoices.reduce((sum, i) => sum + parseFloat(i.total), 0);

            // Update stat cards
            document.getElementById('stat-total-subs').textContent = totalSubs;
            document.getElementById('stat-active-subs').textContent = activeSubs;
            document.getElementById('stat-total-inv').textContent = totalInvoices;
            document.getElementById('stat-pending').textContent = pendingInvoices.length;
            document.getElementById('stat-overdue').textContent = overdueInvoices.length;
            document.getElementById('stat-revenue').textContent = `₹${totalRevenue.toLocaleString()}`;

            // Update recent invoices table
            const recentInvoices = invoices
                .sort((a, b) => new Date(b.issue_date) - new Date(a.issue_date))
                .slice(0, 5);
            this.renderRecentInvoices(recentInvoices);

            // Update recent payments table
            const recentPayments = payments
                .sort((a, b) => new Date(b.paid_on) - new Date(a.paid_on))
                .slice(0, 5);
            this.renderRecentPayments(recentPayments);

        } catch (error) {
            console.error('Error loading overview data:', error);
            document.getElementById('recent-invoices').innerHTML =
                '<tr><td colspan="5" class="empty-state">Failed to load data</td></tr>';
            document.getElementById('recent-payments').innerHTML =
                '<tr><td colspan="4" class="empty-state">Failed to load data</td></tr>';
        }
    }

    renderRecentInvoices(invoices) {
        const tbody = document.getElementById('recent-invoices');
        if (!invoices || invoices.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No invoices found</td></tr>';
            return;
        }

        tbody.innerHTML = invoices.map(inv => `
            <tr>
                <td>${inv.number}</td>
                <td>${inv.customer_name}</td>
                <td>₹${parseFloat(inv.total).toLocaleString()}</td>
                <td><span class="status-badge status-${inv.status}">${inv.status}</span></td>
                <td>${new Date(inv.due_date).toLocaleDateString()}</td>
            </tr>
        `).join('');
    }

    renderRecentPayments(payments) {
        const tbody = document.getElementById('recent-payments');
        if (!payments || payments.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No payments found</td></tr>';
            return;
        }

        tbody.innerHTML = payments.map(p => `
            <tr>
                <td>${new Date(p.paid_on).toLocaleDateString()}</td>
                <td>${p.invoice_number}</td>
                <td>₹${parseFloat(p.amount).toLocaleString()}</td>
                <td>${p.method}</td>
            </tr>
        `).join('');
    }

    // Reference Data Loading
    async loadReferenceData() {
        try {
            const [plans, products, customers] = await Promise.all([
                this.apiGet('/plans'),
                this.apiGet('/products'),
                this.apiGet('/users/customers')
            ]);

            this.plans = plans || [];
            this.products = products || [];
            this.customers = customers || [];

            // Populate plan selects
            const planSelects = document.querySelectorAll('#quotation-plan, #sub-plan');
            planSelects.forEach(select => {
                if (select) {
                    select.innerHTML = this.plans.map(p =>
                        `<option value="${p.id}">${p.name} (₹${parseFloat(p.price).toLocaleString()})</option>`
                    ).join('');
                }
            });

        } catch (error) {
            console.error('Error loading reference data:', error);
            // Use empty arrays as fallback
            this.plans = [];
            this.products = [];
            this.customers = [];
        }
    }

    // Quotations Management
    async loadQuotations() {
        try {
            const templates = await this.apiGet('/quotation-templates');
            const tbody = document.getElementById('quotations-list');
            this.state.quotations = templates;

            if (!templates || templates.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No quotation templates found</td></tr>';
                return;
            }

            tbody.innerHTML = templates.map(t => `
                <tr>
                    <td>${t.id}</td>
                    <td>${t.name}</td>
                    <td>${t.plan_name}</td>
                    <td>${t.validity_days}</td>
                    <td>${t.lines ? t.lines.length : 0}</td>
                    <td>${new Date().toLocaleDateString()}</td>
                    <td class="actions-cell">
                        <button class="action-btn" title="View" onclick="dashboard.viewQuotation(${t.id})"><span>👁️</span></button>
                        <button class="action-btn" title="Edit" onclick="dashboard.editQuotation(${t.id})"><span>✏️</span></button>
                        <button class="action-btn danger" title="Delete" onclick="dashboard.deleteQuotation(${t.id})"><span>🗑️</span></button>
                    </td>
                </tr>
            `).join('');

        } catch (error) {
            console.error('Error loading quotations:', error);
            document.getElementById('quotations-list').innerHTML =
                '<tr><td colspan="7" class="empty-state">Failed to load quotations</td></tr>';
        }
    }

    openQuotationModal(id = null) {
        const modal = document.getElementById('quotation-modal');
        modal.style.display = 'block';
        const form = document.getElementById('create-quotation-form');
        const titleEl = document.getElementById('quotation-modal-title');

        if (id) {
            // Edit mode - load existing data
            titleEl.textContent = 'Edit Quotation Template';
            document.getElementById('edit-quotation-id').value = id;
            this.loadQuotationForEdit(id);
        } else {
            // Create mode
            titleEl.textContent = 'Create Quotation Template';
            form.reset();
            document.getElementById('edit-quotation-id').value = '';
            document.getElementById('quotation-validity').value = 30;
        }
    }

    async loadQuotationForEdit(id) {
        try {
            const template = await this.apiGet(`/quotation-templates/${id}`);
            document.getElementById('quotation-name').value = template.name || '';
            document.getElementById('quotation-plan').value = template.plan_id || '';
            document.getElementById('quotation-validity').value = template.validity_days || 30;
        } catch (error) {
            console.error('Error loading quotation for edit:', error);
            alert(`Error loading quotation: ${error.message}`);
        }
    }

    async createQuotation() {
        const isEdit = document.getElementById('edit-quotation-id').value;
        if (isEdit) {
            await this.updateQuotation(parseInt(isEdit));
        } else {
            await this.saveQuotation();
        }
    }

    async saveQuotation() {
        try {
            const name = document.getElementById('quotation-name').value.trim();
            const planId = parseInt(document.getElementById('quotation-plan').value);
            const validity = parseInt(document.getElementById('quotation-validity').value);

            if (!name || !planId) {
                alert('Please fill in all required fields');
                return;
            }

            await this.apiPost('/quotation-templates', {
                name,
                plan_id: planId,
                validity_days: validity
            });

            this.closeModal('quotation-modal');
            await this.loadQuotations();
            alert('Quotation template created successfully');
        } catch (error) {
            console.error('Error creating quotation:', error);
            alert(`Error: ${error.message}`);
        }
    }

    async updateQuotation(id) {
        try {
            const name = document.getElementById('quotation-name').value.trim();
            const planId = parseInt(document.getElementById('quotation-plan').value);
            const validity = parseInt(document.getElementById('quotation-validity').value);

            if (!name || !planId) {
                alert('Please fill in all required fields');
                return;
            }

            await this.apiPatch(`/quotation-templates/${id}`, {
                name,
                plan_id: planId,
                validity_days: validity
            });

            this.closeModal('quotation-modal');
            await this.loadQuotations();
            alert('Quotation template updated successfully');
        } catch (error) {
            console.error('Error updating quotation:', error);
            alert(`Error: ${error.message}`);
        }
    }

    async deleteQuotation(id) {
        if (confirm('Are you sure you want to delete this quotation template?')) {
            try {
                await this.apiDelete(`/quotation-templates/${id}`);
                await this.loadQuotations();
            } catch (error) {
                console.error('Error deleting quotation:', error);
                alert(`Error: ${error.message}`);
            }
        }
    }

    viewQuotation(id) {
        alert(`View quotation #${id} - Feature not yet implemented`);
    }

    async editQuotation(id) {
        this.openQuotationModal(id);
    }

    // Subscriptions Management
    async loadSubscriptions() {
        try {
            const subs = await this.apiGet('/subscriptions');
            const tbody = document.getElementById('subscriptions-list');
            this.state.subscriptions = subs;

            if (!subs || subs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No subscriptions found</td></tr>';
                return;
            }

            tbody.innerHTML = subs.map(s => `
                <tr>
                    <td>${s.number}</td>
                    <td>${s.customer_name}</td>
                    <td>${s.plan_name}</td>
                    <td><span class="status-badge status-${s.status}">${s.status}</span></td>
                    <td>${new Date(s.start_date).toLocaleDateString()}</td>
                    <td>${new Date(s.expiry_date).toLocaleDateString()}</td>
                    <td class="actions-cell">
                        <button class="action-btn" title="View" onclick="dashboard.viewSubscription(${s.id})"><span>👁️</span></button>
                        <button class="action-btn" title="Pause/Resume" onclick="dashboard.togglePause(${s.id}, ${s.is_paused})"><span>${s.is_paused ? '▶️' : '⏸️'}</span></button>
                        <button class="action-btn" title="Close" onclick="dashboard.closeSubscription(${s.id})"><span>🚪</span></button>
                    </td>
                </tr>
            `).join('');

        } catch (error) {
            console.error('Error loading subscriptions:', error);
            document.getElementById('subscriptions-list').innerHTML =
                '<tr><td colspan="7" class="empty-state">Failed to load subscriptions</td></tr>';
        }
    }

    async openSubscriptionModal() {
        const modal = document.getElementById('subscription-modal');
        modal.style.display = 'block';
        const form = document.getElementById('create-subscription-form');
        form.reset();
        document.getElementById('sub-start-date').valueAsDate = new Date();
        document.getElementById('sub-terms').value = 'net_30';

        // Populate customer dropdown
        try {
            const customers = await this.apiGet('/users/customers');
            const customerSelect = document.getElementById('sub-customer');
            customerSelect.innerHTML = customers.map(c =>
                `<option value="${c.id}">${c.name} (${c.email})</option>`
            ).join('');
            if (customers.length > 0) {
                customerSelect.selectedIndex = 0;
            }
        } catch (error) {
            console.error('Error loading customers:', error);
        }
    }

    async createSubscription() {
        try {
            const customerId = parseInt(document.getElementById('sub-customer').value);
            const planId = parseInt(document.getElementById('sub-plan').value);
            const startDate = document.getElementById('sub-start-date').value;
            const terms = document.getElementById('sub-terms').value;

            if (!customerId || !planId) {
                alert('Please fill in all required fields');
                return;
            }

            await this.apiPost('/subscriptions', {
                customer_id: customerId,
                plan_id: planId,
                start_date: startDate,
                payment_terms: terms,
                lines: []
            });

            this.closeModal('subscription-modal');
            await this.loadSubscriptions();
            alert('Subscription created successfully');
        } catch (error) {
            console.error('Error creating subscription:', error);
            alert(`Error: ${error.message}`);
        }
    }

    async viewSubscription(id) {
        try {
            const sub = await this.apiGet(`/subscriptions/${id}`);
            document.getElementById('sub-detail-title').textContent = `Subscription ${sub.number}`;
            document.getElementById('subscription-detail-content').innerHTML = `
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Status</label>
                        <span><span class="status-badge status-${sub.status}">${sub.status}</span></span>
                    </div>
                    <div class="detail-item">
                        <label>Customer</label>
                        <span>${sub.customer_name}</span>
                    </div>
                    <div class="detail-item">
                        <label>Plan</label>
                        <span>${sub.plan_name}</span>
                    </div>
                    <div class="detail-item">
                        <label>Start Date</label>
                        <span>${new Date(sub.start_date).toLocaleDateString()}</span>
                    </div>
                    <div class="detail-item">
                        <label>Expiry Date</label>
                        <span>${new Date(sub.expiry_date).toLocaleDateString()}</span>
                    </div>
                    <div class="detail-item">
                        <label>Paused</label>
                        <span>${sub.is_paused ? 'Yes' : 'No'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Status Actions</label>
                        <span>
                            <button class="btn btn-secondary" style="font-size: 0.75rem;" onclick="dashboard.togglePause(${sub.id}, ${sub.is_paused})">
                                ${sub.is_paused ? 'Resume' : 'Pause'}
                            </button>
                            ${sub.status === 'draft' ? `<button class="btn btn-primary" style="font-size: 0.75rem; margin-left: 5px;" onclick="dashboard.transitionSubscriptionStatus(${sub.id}, '${sub.status}', 'quotation')">Quote</button>` : ''}
                            ${sub.status === 'quotation' ? `<button class="btn btn-primary" style="font-size: 0.75rem; margin-left: 5px;" onclick="dashboard.transitionSubscriptionStatus(${sub.id}, '${sub.status}', 'confirmed')">Confirm</button>` : ''}
                            ${sub.status === 'confirmed' ? `<button class="btn btn-primary" style="font-size: 0.75rem; margin-left: 5px;" onclick="dashboard.transitionSubscriptionStatus(${sub.id}, '${sub.status}', 'active')">Activate</button>` : ''}
                            ${sub.status !== 'closed' ? `<button class="btn btn-danger" style="font-size: 0.75rem; margin-left: 5px;" onclick="dashboard.closeSubscription(${sub.id})">Close</button>` : ''}
                        </span>
                    </div>
                </div>
                <h4 style="margin-top: 1.5rem; margin-bottom: 1rem;">Subscription Lines</h4>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Product</th>
                            <th>Quantity</th>
                            <th>Unit Price</th>
                            <th>Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${(sub.lines || []).map(line => `
                            <tr>
                                <td>${line.product_name}${line.variant_value ? ` (${line.variant_value})` : ''}</td>
                                <td>${line.quantity}</td>
                                <td>₹${parseFloat(line.unit_price).toLocaleString()}</td>
                                <td>₹${parseFloat(line.amount).toLocaleString()}</td>
                            </tr>
                        `).join('')}
                        ${(sub.lines || []).length === 0 ? '<tr><td colspan="4" class="empty-state">No lines</td></tr>' : ''}
                    </tbody>
                </table>
            `;
            document.getElementById('subscription-detail-modal').style.display = 'block';
        } catch (error) {
            console.error('Error viewing subscription:', error);
            alert(`Error: ${error.message}`);
        }
    }

    async togglePause(id, isPaused) {
        try {
            if (isPaused) {
                await this.apiPost(`/subscriptions/${id}/resume`, {});
                alert('Subscription resumed');
            } else {
                await this.apiPost(`/subscriptions/${id}/pause`, {});
                alert('Subscription paused');
            }
            await this.loadSubscriptions();
            if (this.currentPage === 'overview') {
                await this.loadOverviewData();
            }
        } catch (error) {
            console.error('Error toggling pause:', error);
            alert(`Error: ${error.message}`);
        }
    }

    async closeSubscription(id) {
        if (confirm('Are you sure you want to close this subscription?')) {
            try {
                await this.apiPost(`/subscriptions/${id}/status`, { new_status: 'closed' });
                alert('Subscription closed');
                await this.loadSubscriptions();
                if (this.currentPage === 'overview') {
                    await this.loadOverviewData();
                }
            } catch (error) {
                console.error('Error closing subscription:', error);
                alert(`Error: ${error.message}`);
            }
        }
    }

    // Subscription status transitions
    async transitionSubscriptionStatus(id, fromStatus, toStatus) {
        try {
            await this.apiPost(`/subscriptions/${id}/status`, { new_status: toStatus });
            alert(`Subscription transitioned from ${fromStatus} to ${toStatus}`);
            await this.loadSubscriptions();
            if (this.currentPage === 'overview') {
                await this.loadOverviewData();
            }
        } catch (error) {
            console.error(`Error transitioning subscription:`, error);
            alert(`Error: ${error.message}`);
        }
    }

    // Invoices Management
    async loadInvoices() {
        try {
            const invoices = await this.apiGet('/invoices');
            const tbody = document.getElementById('invoices-list');
            this.state.invoices = invoices;

            if (!invoices || invoices.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No invoices found</td></tr>';
                return;
            }

            tbody.innerHTML = invoices.map(i => `
                <tr>
                    <td>${i.number}</td>
                    <td>${i.customer_name}</td>
                    <td>₹${parseFloat(i.total).toLocaleString()}</td>
                    <td><span class="status-badge status-${i.status}">${i.status}</span></td>
                    <td>${new Date(i.issue_date).toLocaleDateString()}</td>
                    <td>${new Date(i.due_date).toLocaleDateString()}</td>
                    <td class="actions-cell">
                        <button class="action-btn" title="View" onclick="dashboard.viewInvoice(${i.id})"><span>👁️</span></button>
                        ${i.status === 'draft' ? `<button class="action-btn" title="Confirm" onclick="dashboard.confirmInvoice(${i.id})"><span>✅</span></button>` : ''}
                        ${['draft', 'confirmed'].includes(i.status) ? `<button class="action-btn danger" title="Cancel" onclick="dashboard.cancelInvoice(${i.id})"><span>🚫</span></button>` : ''}
                        ${i.status === 'paid' ? `<button class="action-btn" title="Print" onclick="dashboard.printInvoice(${i.id})"><span>🖨️</span></button>` : ''}
                    </td>
                </tr>
            `).join('');

        } catch (error) {
            console.error('Error loading invoices:', error);
            document.getElementById('invoices-list').innerHTML =
                '<tr><td colspan="7" class="empty-state">Failed to load invoices</td></tr>';
        }
    }

    async openInvoiceModal() {
        const modal = document.getElementById('invoice-modal');
        modal.style.display = 'block';
        const form = document.getElementById('create-invoice-form');
        const today = new Date();

        // Populate subscription dropdown
        try {
            const subs = await this.apiGet('/subscriptions');
            const subSelect = document.getElementById('invoice-subscription');
            subSelect.innerHTML = subs.map(s =>
                `<option value="${s.id}">${s.number} - ${s.customer_name}</option>`
            ).join('');
            if (subs.length > 0) {
                subSelect.selectedIndex = 0;
            }
        } catch (error) {
            console.error('Error loading subscriptions for invoice:', error);
        }

        form.reset();
        document.getElementById('invoice-period-start').valueAsDate = today;
        document.getElementById('invoice-period-end').valueAsDate = today;
        document.getElementById('invoice-issue-date').valueAsDate = today;
        document.getElementById('invoice-due-date').valueAsDate = new Date(today.getTime() + 30 * 24 * 60 * 60 * 1000);
    }

    async createInvoice() {
        try {
            const subscriptionId = parseInt(document.getElementById('invoice-subscription').value);
            const periodStart = document.getElementById('invoice-period-start').value;
            const periodEnd = document.getElementById('invoice-period-end').value;
            const issueDate = document.getElementById('invoice-issue-date').value;
            const dueDate = document.getElementById('invoice-due-date').value;

            if (!subscriptionId) {
                alert('Please select a subscription');
                return;
            }

            const result = await this.apiPost('/invoices', {
                subscription_id: subscriptionId,
                period_start: periodStart,
                period_end: periodEnd,
                issue_date: issueDate,
                due_date: dueDate
            });

            this.closeModal('invoice-modal');
            await this.loadInvoices();
            if (this.currentPage === 'overview') {
                await this.loadOverviewData();
            }
            alert('Invoice generated successfully');
        } catch (error) {
            console.error('Error creating invoice:', error);
            alert(`Error: ${error.message}\n\nSubscription must be ACTIVE to generate an invoice. Use the status buttons in the subscription details to transition: Draft → Quotation → Confirmed → Active.`);
        }
    }

    async viewInvoice(id) {
        try {
            const invoice = await this.apiGet(`/invoices/${id}`);
            const outstanding = await this.apiGet(`/invoices/${id}/outstanding`);
            document.getElementById('invoice-detail-title').textContent = `Invoice ${invoice.number}`;
            document.getElementById('invoice-detail-content').innerHTML = `
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Status</label>
                        <span><span class="status-badge status-${invoice.status}">${invoice.status}</span></span>
                    </div>
                    <div class="detail-item">
                        <label>Customer</label>
                        <span>${invoice.customer_name}</span>
                    </div>
                    <div class="detail-item">
                        <label>Subscription</label>
                        <span>${invoice.subscription_number}</span>
                    </div>
                    <div class="detail-item">
                        <label>Issue Date</label>
                        <span>${new Date(invoice.issue_date).toLocaleDateString()}</span>
                    </div>
                    <div class="detail-item">
                        <label>Due Date</label>
                        <span>${new Date(invoice.due_date).toLocaleDateString()}</span>
                    </div>
                    <div class="detail-item">
                        <label>Total</label>
                        <span>₹${parseFloat(invoice.total).toLocaleString()}</span>
                    </div>
                    <div class="detail-item">
                        <label>Amount Paid</label>
                        <span>₹${parseFloat(invoice.amount_paid).toLocaleString()}</span>
                    </div>
                    <div class="detail-item">
                        <label>Outstanding</label>
                        <span>₹${parseFloat(outstanding.outstanding).toLocaleString()}</span>
                    </div>
                </div>
                <h4 style="margin-top: 1.5rem; margin-bottom: 1rem;">Invoice Lines</h4>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Product</th>
                            <th>Description</th>
                            <th>Qty</th>
                            <th>Unit Price</th>
                            <th>Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${(invoice.lines || []).map(line => `
                            <tr>
                                <td>${line.product_name}</td>
                                <td>${line.description || ''}</td>
                                <td>${line.quantity}</td>
                                <td>₹${parseFloat(line.unit_price).toLocaleString()}</td>
                                <td>₹${parseFloat(line.amount).toLocaleString()}</td>
                            </tr>
                        `).join('')}
                        ${(invoice.lines || []).length === 0 ? '<tr><td colspan="5" class="empty-state">No lines</td></tr>' : ''}
                    </tbody>
                </table>
                <div style="margin-top: 1rem; padding: 1rem; background-color: #f9fafb; border-radius: 8px;">
                    <strong>Summary</strong>
                    <div style="display: flex; justify-content: space-between; margin-top: 0.5rem;">
                        <span>Subtotal: ₹${parseFloat(invoice.subtotal).toLocaleString()}</span>
                        <span>Discount: ₹${parseFloat(invoice.discount_total).toLocaleString()}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-top: 0.25rem;">
                        <span>Tax: ₹${parseFloat(invoice.tax_total).toLocaleString()}</span>
                        <strong>Total: ₹${parseFloat(invoice.total).toLocaleString()}</strong>
                    </div>
                    ${invoice.status !== 'paid' && parseFloat(invoice.outstanding || 0) > 0 ?
                        `<div style="display: flex; justify-content: space-between; margin-top: 0.25rem;">
                            <span>Amount Paid: ₹${parseFloat(invoice.amount_paid).toLocaleString()}</span>
                            <span style="color: #f59e0b; font-weight: 600;">Outstanding: ₹${parseFloat(outstanding.outstanding).toLocaleString()}</span>
                        </div>` : ''
                    }
                </div>
            `;
            document.getElementById('invoice-detail-modal').style.display = 'block';
        } catch (error) {
            console.error('Error viewing invoice:', error);
            alert(`Error: ${error.message}`);
        }
    }

    async confirmInvoice(id) {
        try {
            await this.apiPost(`/invoices/${id}/confirm`, {});
            alert('Invoice confirmed');
            await this.loadInvoices();
            if (this.currentPage === 'overview') {
                await this.loadOverviewData();
            }
        } catch (error) {
            console.error('Error confirming invoice:', error);
            alert(`Error: ${error.message}`);
        }
    }

    async cancelInvoice(id) {
        if (confirm('Are you sure you want to cancel this invoice?')) {
            try {
                await this.apiPost(`/invoices/${id}/cancel`, {});
                alert('Invoice cancelled');
                await this.loadInvoices();
                if (this.currentPage === 'overview') {
                    await this.loadOverviewData();
                }
            } catch (error) {
                console.error('Error cancelling invoice:', error);
                alert(`Error: ${error.message}`);
            }
        }
    }

    printInvoice(id) {
        // Create a print-friendly invoice view
        const invoice = this.state.invoices.find(i => i.id === id);
        if (!invoice) {
            alert('Invoice not found');
            return;
        }

        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Invoice ${invoice.number}</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .invoice-header { text-align: center; margin-bottom: 30px; }
                    .invoice-title { font-size: 24px; font-weight: bold; }
                    .invoice-id { font-size: 14px; color: #666; }
                    .invoice-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
                    .invoice-table th, .invoice-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    .invoice-table th { background-color: #f4f4f4; }
                    .totals { width: 300px; float: right; }
                    .total-row { display: flex; justify-content: space-between; padding: 8px 0; }
                    .total-label { font-weight: bold; }
                </style>
            </head>
            <body>
                <div class="invoice-header">
                    <div class="invoice-title">INVOICE</div>
                    <div class="invoice-id">${invoice.number}</div>
                    <div>Issue Date: ${new Date(invoice.issue_date).toLocaleDateString()}</div>
                    <div>Due Date: ${new Date(invoice.due_date).toLocaleDateString()}</div>
                </div>
                <table class="invoice-table">
                    <thead>
                        <tr>
                            <th>Description</th>
                            <th>Qty</th>
                            <th>Unit Price</th>
                            <th>Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${(invoice.lines || []).map(line => `
                            <tr>
                                <td>${line.description || line.product_name}</td>
                                <td>${line.quantity}</td>
                                <td>₹${parseFloat(line.unit_price).toLocaleString()}</td>
                                <td>₹${parseFloat(line.amount).toLocaleString()}</td>
                            </tr>
                        `).join('')}
                        ${(invoice.lines || []).length === 0 ? '<tr><td colspan="4" class="empty-state">No line items</td></tr>' : ''}
                    </tbody>
                </table>
                <div class="totals">
                    <div class="total-row"><span class="total-label">Subtotal:</span><span>₹${parseFloat(invoice.subtotal).toLocaleString()}</span></div>
                    <div class="total-row"><span class="total-label">Tax:</span><span>₹${parseFloat(invoice.tax_total).toLocaleString()}</span></div>
                    <div class="total-row"><span class="total-label">Discount:</span><span>₹${parseFloat(invoice.discount_total).toLocaleString()}</span></div>
                    <div class="total-row"><span class="total-label">Total:</span><span>₹${parseFloat(invoice.total).toLocaleString()}</span></div>
                </div>
            </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.focus();
        printWindow.print();
    }

    // Payments Management
    async loadPayments() {
        try {
            const payments = await this.apiGet('/payments');
            const tbody = document.getElementById('payments-list');
            this.state.payments = payments;

            if (!payments || payments.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No payments found</td></tr>';
            } else {
                tbody.innerHTML = payments.map(p => `
                    <tr>
                        <td>${new Date(p.paid_on).toLocaleDateString()}</td>
                        <td>${p.invoice_number}</td>
                        <td>₹${parseFloat(p.amount).toLocaleString()}</td>
                        <td>${p.method}</td>
                        <td class="actions-cell">
                            <button class="action-btn" title="View Details" onclick="dashboard.viewPayment(${p.id})"><span>👁️</span></button>
                        </td>
                    </tr>
                `).join('');
            }

            // Populate invoice dropdown for new payments
            const invoices = await this.apiGet('/invoices');
            const paymentSelect = document.getElementById('payment-invoice');
            paymentSelect.innerHTML = invoices.map(inv =>
                `<option value="${inv.id}">${inv.number} - ₹${parseFloat(inv.total).toLocaleString()}</option>`
            ).join('');

        } catch (error) {
            console.error('Error loading payments:', error);
            document.getElementById('payments-list').innerHTML =
                '<tr><td colspan="5" class="empty-state">Failed to load payments</td></tr>';
        }
    }

    openPaymentModal() {
        const modal = document.getElementById('payment-modal');
        modal.style.display = 'block';
        const form = document.getElementById('create-payment-form');
        form.reset();
        document.getElementById('payment-date').valueAsDate = new Date();
    }

    async createPayment() {
        try {
            const invoiceId = parseInt(document.getElementById('payment-invoice').value);
            const amount = parseFloat(document.getElementById('payment-amount').value);
            const method = document.getElementById('payment-method').value;
            const paidOn = document.getElementById('payment-date').value;
            const note = document.getElementById('payment-note').value.trim();

            if (!invoiceId || !amount || !method) {
                alert('Please fill in all required fields');
                return;
            }

            await this.apiPost('/payments', {
                invoice_id: invoiceId,
                amount: amount,
                method: method,
                paid_on: paidOn,
                note: note
            });

            this.closeModal('payment-modal');
            await this.loadPayments();
            if (this.currentPage === 'overview') {
                await this.loadOverviewData();
            }
            alert('Payment recorded successfully');
        } catch (error) {
            console.error('Error recording payment:', error);
            alert(`Error: ${error.message}`);
        }
    }

    async viewPayment(id) {
        try {
            const payment = await this.apiGet(`/payments/${id}`);
            alert(`Payment Details:\nInvoice: ${payment.invoice_number}\nAmount: ₹${parseFloat(payment.amount).toLocaleString()}\nMethod: ${payment.method}\nDate: ${new Date(payment.paid_on).toLocaleDateString()}\nNote: ${payment.note || 'N/A'}`);
        } catch (error) {
            console.error('Error viewing payment:', error);
            alert(`Error: ${error.message}`);
        }
    }

    // Utility Methods
    closeModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new SubscriptionDashboard();
});