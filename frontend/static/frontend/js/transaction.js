
document.addEventListener("DOMContentLoaded", () => {
    fetchTransactions();
    fetchCategories();
});

document.getElementById("addTransactionBtn").addEventListener("click", () => {
    document.getElementById("addTransactionModal").classList.remove("hidden");
});
document.getElementById("closeModal").addEventListener("click", () => {
    document.getElementById("addTransactionModal").classList.add("hidden");
});

document.getElementById("transactionForm").addEventListener("submit", async function(event) {
    event.preventDefault();
    const newTransaction = {
        date: document.getElementById("transactionDate").value,
        category_id: document.getElementById("transactionCategory").value,
        amount: parseFloat(document.getElementById("transactionAmount").value),
        currency: document.getElementById("transactionCurrency").value,
        description: document.getElementById("transactionDescription").value,
    };
    try {
        await fetch("/api/transactions/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(newTransaction),
        });
        fetchTransactions();
        document.getElementById("addTransactionModal").classList.add("hidden");
    } catch (error) {
        console.error("Error adding transaction:", error);
    }
});

async function fetchTransactions() {
    try {
        const response = await fetch("/api/transactions/");
        const transactions = await response.json();
        renderTransactions(transactions);
    } catch (error) {
        console.error("Error fetching transactions:", error);
    }
}

function renderTransactions(transactions) {
    const tbody = document.getElementById("transactionsList");
    tbody.innerHTML = transactions.map(t => `
        <tr class="border-b">
            <td>${t.date}</td>
            <td>${t.category_type}</td>
            <td class="text-right">$${t.amount.toFixed(2)}</td>
            <td>${t.currency}</td>
            <td>${t.description}</td>
            <td class="text-center">
                <button onclick="deleteTransaction(${t.id})" class="text-red-600">Delete</button>
            </td>
        </tr>
    `).join('');
}


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


    document.getElementById("transactionForm").addEventListener("submit", async function(event) {
        event.preventDefault();
        const newTransaction = {
            date: document.getElementById("transactionDate").value,
            category_id: document.getElementById("transactionCategory").value,
            amount: parseFloat(document.getElementById("transactionAmount").value),
            currency: document.getElementById("transactionCurrency").value,
            description: document.getElementById("transactionDescription").value,
        };
        try {
            await fetch("/api/transactions/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(newTransaction),
            });
            fetchTransactions();
            document.getElementById("addTransactionModal").classList.add("hidden");
        } catch (error) {
            console.error("Error adding transaction:", error);
        }
    });
    