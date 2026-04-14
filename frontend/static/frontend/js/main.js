const voiceEntryBtn = document.getElementById('voiceEntryBtn');
const transactionModal = document.getElementById('transactionModal');
const editAmount = document.getElementById('editAmount');
const editCategory = document.getElementById('editCategory');
const editType = document.getElementById('editType');
const saveTransactionBtn = document.getElementById('saveTransaction');
const cancelTransactionBtn = document.getElementById('cancelTransaction');

    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();

        recognition.continuous = false;
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        voiceEntryBtn.addEventListener('click', () => {
            recognition.start();
            alert("Listening... Speak your transaction details.");
        });

        recognition.onresult = async (event) => {
            const voiceText = event.results[0][0].transcript;
            console.log("Voice Input:", voiceText);

            // Show loading
            voiceEntryBtn.textContent = "Processing...";
            voiceEntryBtn.disabled = true;

            const response = await fetch('/api/process-voice/', {
                method: 'POST',
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ voice_text: voiceText })
            });

            voiceEntryBtn.textContent = "Voice Entry";
            voiceEntryBtn.disabled = false;

            const data = await response.json();

            if (data.error) {
                alert("Error processing voice input.");
                return;
            }

            // Populate transaction details in modal
            editAmount.value = data.amount;
            editCategory.value = data.category;
            editType.value = data.transaction_type;

            transactionModal.classList.remove('hidden');
        };

        recognition.onerror = (event) => {
            alert("Voice recognition error: " + event.error);
        };
    }

    // Handle transaction save
    saveTransactionBtn.addEventListener('click', async () => {
        const transactionData = {
            amount: parseFloat(editAmount.value),
            transaction_type: editType.value,
            category: editCategory.value
        };

        const response = await fetch('/api/confirm-transaction/', {
            method: 'POST',
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(transactionData)
        });

        const result = await response.json();

        if (result.message) {
            alert("Transaction saved successfully!");
            transactionModal.classList.add('hidden');
        } else {
            alert("Error saving transaction.");
        }
    });

    cancelTransactionBtn.addEventListener('click', () => {
        transactionModal.classList.add('hidden');
    });

    // Fetch User Data from API
    
    async function fetchUserProfile() {
        try {
            const response = await fetch('/api/user-profile/');
            const data = await response.json();
            document.getElementById('userAvatar').src = data.avatar;
            document.getElementById('userName').textContent = data.username;
            document.getElementById('currentDate').textContent = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
        } catch (error) {
            console.error('Error fetching user profile:', error);
        }
    }



    // Toggle User Dropdown Menu
    document.getElementById('userDropdownBtn').addEventListener('click', () => {
        document.getElementById('userDropdown').classList.toggle('hidden');
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (event) => {
        const dropdown = document.getElementById('userDropdown');
        if (!document.getElementById('userDropdownBtn').contains(event.target) && !dropdown.contains(event.target)) {
            dropdown.classList.add('hidden');
        }
    });

    // Set Savings Progress Bar Width
    document.getElementById('savingsProgressBar').style.width = '{{ savings_progress }}%';

    // Load User Data on Page Load
    fetchUserProfile();

    // Embed Django data into JavaScript variables
    const spendingData = JSON.parse('{{ spending_data|safe }}');

    const spendingChart = echarts.init(document.getElementById('spendingChart'));
    const expensePieChart = echarts.init(document.getElementById('expensePieChart'));
    const expenseBarChart = echarts.init(document.getElementById('expenseBarChart'));

    function updateCharts(data) {
        // Line Chart (Income vs. Expenses)
        spendingChart.setOption({
            tooltip: { trigger: 'axis' },
            legend: { data: ['Income', 'Expenses'] },
            xAxis: { type: 'category', data: data.dates },
            yAxis: { type: 'value' },
            series: [
                { name: 'Income', type: 'line', data: data.income, smooth: true },
                { name: 'Expenses', type: 'line', data: data.expenses, smooth: true }
            ]
        });

        // Pie Chart (Category-wise Expense Distribution)
        expensePieChart.setOption({
            tooltip: { trigger: 'item' },
            legend: { bottom: 10, left: 'center' },
            series: [{
                name: 'Expenses by Category',
                type: 'pie',
                radius: '50%',
                data: data.expense_categories.map(item => ({ name: item.category, value: item.amount }))
            }]
        });

        // Bar Chart (Monthly Expenses Breakdown)
        expenseBarChart.setOption({
            tooltip: { trigger: 'axis' },
            xAxis: { type: 'category', data: data.months },
            yAxis: { type: 'value' },
            series: [{ name: 'Monthly Expenses', type: 'bar', data: data.monthly_expenses }]
        });
    }

    // Load data on page load
    updateCharts(spendingData);

    // Event listeners for filtering
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.replace('bg-primary', 'bg-gray-100'));
            btn.classList.replace('bg-gray-100', 'bg-primary');

            fetch(`/spending-analysis/?period=${btn.getAttribute('data-period')}`)
                .then(response => response.json())
                .then(data => updateCharts(data));
        });
    });

    // Resize charts on window resize
    window.addEventListener('resize', () => {
        spendingChart.resize();
        expensePieChart.resize();
        expenseBarChart.resize();
    });



    async function fetchTransactions() {
        try {
            const response = await fetch('/api/transactions/');
            const transactions = await response.json();
            const transactionList = document.getElementById('transactionList');

            // Clear existing content
            transactionList.innerHTML = '';

            transactions.forEach(transaction => {
                let iconClass = "ri-file-list-line text-gray-600";  // Default icon
                let bgClass = "bg-gray-100";
                let amountClass = "text-red-600"; // Default to expense

                // Categorizing transactions
                switch (transaction.category_name.toLowerCase()) {
                    case "salary":
                        iconClass = "ri-bank-line text-green-600";
                        bgClass = "bg-green-100";
                        amountClass = "text-green-600"; // Income
                        break;
                    case "freelance":
                        iconClass = "ri-briefcase-line text-green-600";
                        bgClass = "bg-green-100";
                        amountClass = "text-green-600"; // Income
                        break;
                    case "investment":
                        iconClass = "ri-stock-line text-green-600";
                        bgClass = "bg-green-100";
                        amountClass = "text-green-600"; // Income
                        break;
                    case "bonus":
                        iconClass = "ri-gift-line text-green-600";
                        bgClass = "bg-green-100";
                        amountClass = "text-green-600"; // Income
                        break;
                    case "subscription":
                        iconClass = "ri-netflix-fill text-purple-600";
                        bgClass = "bg-purple-100";
                        break;
                    case "netflix":
                        iconClass = "ri-netflix-fill text-red-600";
                        bgClass = "bg-red-100";
                        break;
                    case "spotify":
                        iconClass = "ri-spotify-line text-green-600";
                        bgClass = "bg-green-100";
                        break;
                    case "amazon prime":
                        iconClass = "ri-amazon-fill text-blue-600";
                        bgClass = "bg-blue-100";
                        break;
                    case "hulu":
                        iconClass = "ri-hulu-fill text-green-600";
                        bgClass = "bg-green-100";
                        break;
                    case "disney plus":
                        iconClass = "ri-disney-fill text-blue-600";
                        bgClass = "bg-blue-100";
                        break;
                    case "shopping":
                        iconClass = "ri-shopping-bag-line text-blue-600";
                        bgClass = "bg-blue-100";
                        break;
                    case "groceries":
                        iconClass = "ri-store-line text-blue-600";
                        bgClass = "bg-blue-100";
                        break;
                    case "restaurant":
                    case "food":
                    case "dining":
                        iconClass = "ri-restaurant-line text-orange-600";
                        bgClass = "bg-orange-100";
                        break;
                    case "transport":
                    case "fuel":
                    case "travel":
                        iconClass = "ri-car-line text-orange-600";
                        bgClass = "bg-orange-100";
                        break;
                    case "education":
                    case "courses":
                    case "books":
                        iconClass = "ri-book-line text-indigo-600";
                        bgClass = "bg-indigo-100";
                        break;
                    case "entertainment":
                    case "movies":
                    case "gaming":
                        iconClass = "ri-movie-line text-red-600";
                        bgClass = "bg-red-100";
                        break;
                    case "health":
                    case "medical":
                    case "insurance":
                        iconClass = "ri-hospital-line text-red-600";
                        bgClass = "bg-red-100";
                        break;
                    case "utilities":
                    case "electricity":
                    case "water":
                    case "internet":
                    case "phone":
                        iconClass = "ri-flashlight-line text-yellow-600";
                        bgClass = "bg-yellow-100";
                        break;
                    case "rent":
                    case "mortgage":
                    case "household":
                        iconClass = "ri-home-line text-teal-600";
                        bgClass = "bg-teal-100";
                        break;
                    case "charity":
                    case "donation":
                        iconClass = "ri-heart-line text-pink-600";
                        bgClass = "bg-pink-100";
                        break;
                    case "debt":
                    case "loan":
                    case "credit card":
                        iconClass = "ri-money-dollar-box-line text-gray-600";
                        bgClass = "bg-gray-100";
                        break;
                    default:
                        iconClass = "ri-file-list-line text-gray-600";  // Default icon
                        bgClass = "bg-gray-100";
                        break;
                }

                // Format amount
                const formattedAmount = `₹${parseFloat(transaction.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

                // Create transaction item
                const transactionItem = `
                    <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div class="flex items-center">
                            <div class="w-10 h-10 ${bgClass} rounded-full flex items-center justify-center mr-4">
                                <i class="${iconClass}"></i>
                            </div>
                            <div>
                                <p class="font-medium text-gray-900">${transaction.description}</p>
                                <p class="text-sm text-gray-500">${transaction.category_name} - ${new Date(transaction.date).toLocaleDateString()}</p>
                            </div>
                        </div>
                        <p class="font-medium ${amountClass}">${transaction.category_type === "income" ? "+" : "-"}${formattedAmount}</p>
                    </div>
                `;

                transactionList.innerHTML += transactionItem;
            });

        } catch (error) {
            console.error('Error fetching transactions:', error);
        }
    }

    // Fetch transactions on page load
    fetchTransactions();


    async function fetchAIInsights() {
        try {
            const response = await fetch('/api/ai-insights/');
            const data = await response.json();

            document.getElementById('aiInsightsBox').innerHTML = '';

            data.forEach(insight => {
                document.getElementById('aiInsightsBox').innerHTML += `
                    <div class="p-4 bg-blue-50 rounded-lg mb-4">
                        <p class="font-medium text-gray-900 mb-2">${insight.title}</p>
                        <p class="text-sm text-gray-600 mb-4">${insight.message}</p>
                        <button class="acceptBudgetBtn text-sm font-medium text-primary" 
                            data-category="${insight.category}" 
                            data-budget="${insight.suggested_budget}">
                            Accept Suggested Budget (₹${insight.suggested_budget})
                        </button>
                    </div>
                `;
            });

            // Attach event listeners to "Accept Suggested Budget" buttons
            document.querySelectorAll('.acceptBudgetBtn').forEach(btn => {
                btn.addEventListener('click', function () {
                    acceptSuggestedBudget(this.getAttribute('data-category'), this.getAttribute('data-budget'));
                });
            });

        } catch (error) {
            console.error('Error fetching AI insights:', error);
        }
    }

    fetchAIInsights();

    async function acceptSuggestedBudget(category, newLimit) {
        const response = await fetch('/api/accept-suggested-budget/', {
            method: 'POST',
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ category, new_limit: newLimit })
        });

        const result = await response.json();

        if (result.message) {
            alert(result.message);
            fetchAIInsights(); // Refresh insights after updating budget
        } else {
            alert("Error updating budget.");
        }
    }

   
    
        async function fetchUpcomingBills() {
            try {
                const response = await fetch('/api/upcoming-bills/');
                const bills = await response.json();
                const billsList = document.getElementById('billsList');
    
                billsList.innerHTML = '';
    
                bills.forEach(bill => {
                    let textColor = bill.days_remaining <= 7 ? "text-red-600" : "text-gray-900";
                    let formattedAmount = `₹${bill.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
                    
                    billsList.innerHTML += `
                        <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                            <div>
                                <p class="font-medium ${textColor}">${bill.name} (${bill.category})</p>
                                <p class="text-sm text-gray-500">${bill.frequency} - Due in ${bill.days_remaining} days (${bill.next_payment_date})</p>
                            </div>
                            <p class="font-medium ${textColor}">${formattedAmount}</p>
                        </div>
                    `;
                });
    
            } catch (error) {
                console.error('Error fetching upcoming bills:', error);
            }
        }
    
        fetchUpcomingBills();
    
        
            async function fetchUserNotifications() {
                try {
                    const response = await fetch('/api/user-notifications/');
                    const data = await response.json();
                    const notificationList = document.getElementById('notificationList');
                    const notificationBadge = document.getElementById('notificationBadge');
        
                    notificationList.innerHTML = '';
                    if (data.length > 0) {
                        notificationBadge.classList.remove('hidden'); // Show red dot
                        data.forEach(notification => {
                            notificationList.innerHTML += `
                                <div class="p-2 bg-gray-50 rounded">
                                    <p class="font-medium text-gray-900">${notification.title}</p>
                                    <p class="text-sm text-gray-600">${notification.message}</p>
                                    <p class="text-xs text-gray-500">${notification.timestamp}</p>
                                </div>
                            `;
                        });
                    } else {
                        notificationList.innerHTML = `<p class="text-sm text-gray-500">No new notifications.</p>`;
                    }
                } catch (error) {
                    console.error('Error fetching notifications:', error);
                }
            }
        
            // Show/Hide Notifications
            document.getElementById('notificationBtn').addEventListener('click', () => {
                document.getElementById('notificationDropdown').classList.toggle('hidden');
                fetchUserNotifications();
            });
        
            fetchUserNotifications(); // Load on page load
        
           