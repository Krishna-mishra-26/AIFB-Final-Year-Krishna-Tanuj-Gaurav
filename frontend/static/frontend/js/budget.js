
        function initializeDashboard() {
            setCurrentMonth();
            fetchBudgetData();
            fetchTransactions();
            fetchBudgetInsights();
        }

        async function fetchBudgetInsights() {
            let response = await fetch('/api/budget-insights/');
            let data = await response.json();
            let warnings = "";
            
            data.forEach(insight => {
                if (insight.forecasted_spending > insight.average_spending) {
                    warnings += `<p>⚠️ High spending detected in <b>${insight.category}</b>. AI suggests: ${insight.savings_recommendation} <button onclick='showReallocationModal("${insight.category}", ${insight.suggested_limit})' class='text-blue-500 underline hover:text-blue-600 transition duration-300'>Adjust Budget</button></p>`;
                }
            });
            document.getElementById('budgetWarnings').innerHTML = warnings;
        }

        function showReallocationModal(category, suggestedLimit) {
            document.getElementById('aiSuggestionText').innerHTML = `AI suggests reallocating <b>${category}</b> budget to $${suggestedLimit}. Do you approve?`;
            document.getElementById('aiReallocateModal').classList.remove('hidden');
        }

        function confirmReallocation(approved) {
            if (approved) {
                alert("Budget reallocated successfully!");
            }
            document.getElementById('aiReallocateModal').classList.add('hidden');
        }
    