USE shopsense_ai;
SELECT COUNT(*) AS total_transactions
FROM sales;
SELECT 
    SUM(total_amount) AS total_revenue
FROM sales;
SELECT 
    ROUND(AVG(total_amount), 2) AS average_bill_value
FROM sales;
SELECT
    MIN(total_amount) AS minimum_bill,
    MAX(total_amount) AS maximum_bill
FROM sales;
SELECT
    payment_method,
    COUNT(*) AS transactions,
    SUM(total_amount) AS revenue
FROM sales
GROUP BY payment_method
ORDER BY revenue DESC;
SELECT
    DATE(sale_datetime) AS sale_date,
    COUNT(*) AS transactions,
    SUM(total_amount) AS revenue
FROM sales
GROUP BY DATE(sale_datetime)
ORDER BY sale_date;
SELECT
    p.product_name,
    SUM(si.quantity) AS total_quantity_sold,
    SUM(si.total) AS revenue
FROM sale_items si
JOIN products p
    ON si.product_id = p.product_id
GROUP BY p.product_name
ORDER BY total_quantity_sold DESC;
SELECT
    p.product_name,
    SUM(si.total) AS total_revenue
FROM sale_items si
JOIN products p
    ON si.product_id = p.product_id
GROUP BY p.product_name
ORDER BY total_revenue DESC;
SELECT
    p.product_name,

    SUM(si.quantity) AS quantity_sold,

    SUM(si.quantity * p.cost_price) AS total_cost,

    SUM(si.total) AS revenue,

    SUM(
        si.total - (si.quantity * p.cost_price)
    ) AS gross_profit

FROM sale_items si

JOIN products p
    ON si.product_id = p.product_id

GROUP BY p.product_name

ORDER BY gross_profit DESC;
SELECT
    HOUR(sale_datetime) AS sale_hour,
    COUNT(*) AS transactions,
    SUM(total_amount) AS revenue
FROM sales
GROUP BY HOUR(sale_datetime)
ORDER BY sale_hour;
SELECT
    DAYNAME(sale_datetime) AS day_name,
    COUNT(*) AS transactions,
    SUM(total_amount) AS revenue
FROM sales
GROUP BY DAYNAME(sale_datetime)
ORDER BY revenue DESC;
SELECT
    DATE(sale_datetime) AS sale_date,
    COUNT(*) AS transactions,
    SUM(total_amount) AS revenue
FROM sales
GROUP BY DATE(sale_datetime)
ORDER BY revenue DESC
LIMIT 1;
SELECT
    DATE(sale_datetime) AS sale_date,
    COUNT(*) AS transactions,
    SUM(total_amount) AS revenue
FROM sales
GROUP BY DATE(sale_datetime)
ORDER BY revenue ASC
LIMIT 1;
SELECT
    ROUND(AVG(daily_revenue), 2) AS average_daily_revenue
FROM (
    SELECT
        DATE(sale_datetime) AS sale_date,
        SUM(total_amount) AS daily_revenue
    FROM sales
    GROUP BY DATE(sale_datetime)
) AS daily_sales;
SELECT
    COUNT(*) AS total_transactions,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS average_bill,
    ROUND(MIN(total_amount), 2) AS minimum_bill,
    ROUND(MAX(total_amount), 2) AS maximum_bill
FROM sales;