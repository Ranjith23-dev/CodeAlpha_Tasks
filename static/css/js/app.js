document.addEventListener('DOMContentLoaded', () => {
    const quantityInputs = document.querySelectorAll('input[type="number"]');
    quantityInputs.forEach((input) => {
        input.addEventListener('change', () => {
            if (parseInt(input.value || '0', 10) < 0) {
                input.value = 0;
            }
        });
    });
});
