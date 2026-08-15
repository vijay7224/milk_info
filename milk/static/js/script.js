document.addEventListener(
    "DOMContentLoaded",
    function () {

        const quantity =
            document.getElementById(
                "quantity"
            );

        const price =
            document.getElementById(
                "price"
            );

        const total =
            document.getElementById(
                "total"
            );


        function calculateTotal() {

            const q =
                parseFloat(
                    quantity.value
                ) || 0;


            const p =
                parseFloat(
                    price.value
                ) || 0;


            const result =
                q * p;


            total.textContent =
                result.toFixed(2);

        }


        if (
            quantity &&
            price &&
            total
        ) {

            quantity.addEventListener(
                "input",
                calculateTotal
            );


            price.addEventListener(
                "input",
                calculateTotal
            );


            calculateTotal();

        }

    }
);