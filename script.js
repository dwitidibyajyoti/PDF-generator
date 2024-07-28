document.getElementById('pdfForm').addEventListener('submit', function (event) {
    event.preventDefault();

    const name = document.getElementById('name').value;
    const companyName = document.getElementById('company_name').value;
    const regDate = document.getElementById('reg_date').value;
    const issueDate = document.getElementById('issue_date').value;
    const expiryDate = document.getElementById('expiry_date').value;
    const type = document.getElementById('type').value;
    const category = document.getElementById('category').value;

    fetch('http://127.0.0.1:5000/generate-pdf', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            name: name,
            company_name: companyName,
            reg_date: regDate,
            issue_date: issueDate,
            expiry_date: expiryDate,
            type: type,
            category: category
        }),
    })
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'generated.pdf';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => console.error('Error:', error));
});
