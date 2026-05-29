from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mysqldb import MySQL
import MySQLdb
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# MySQL Configuration
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', 'password')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'stock_management')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


def init_db():
    """Initialize database tables"""
    try:
        cur = mysql.connection.cursor()

        cur.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sku VARCHAR(50) NOT NULL UNIQUE,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                category_id INT,
                quantity INT DEFAULT 0,
                unit_price DECIMAL(10, 2) NOT NULL,
                cost_price DECIMAL(10, 2) NOT NULL,
                reorder_level INT DEFAULT 10,
                supplier VARCHAR(200),
                location VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                product_id INT NOT NULL,
                type ENUM('IN', 'OUT', 'ADJUSTMENT') NOT NULL,
                quantity INT NOT NULL,
                reference VARCHAR(100),
                notes TEXT,
                user VARCHAR(100) DEFAULT 'Admin',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        ''')

        # Seed categories if empty
        cur.execute('SELECT COUNT(*) as cnt FROM categories')
        if cur.fetchone()['cnt'] == 0:
            categories = [
                ('Electronics', 'Electronic components and devices'),
                ('Office Supplies', 'Office stationery and supplies'),
                ('Raw Materials', 'Production raw materials'),
                ('Finished Goods', 'Ready-to-sell products'),
                ('Packaging', 'Packaging materials'),
            ]
            cur.executemany('INSERT INTO categories (name, description) VALUES (%s, %s)', categories)

        # Seed products if empty
        cur.execute('SELECT COUNT(*) as cnt FROM products')
        if cur.fetchone()['cnt'] == 0:
            products = [
                ('SKU-001', 'Laptop Pro 15"', 'High performance laptop', 1, 45, 1299.99, 950.00, 5, 'TechSupplier Inc', 'Shelf A1'),
                ('SKU-002', 'Wireless Mouse', 'Ergonomic wireless mouse', 1, 120, 49.99, 22.00, 20, 'TechSupplier Inc', 'Shelf A2'),
                ('SKU-003', 'Office Chair', 'Ergonomic office chair', 2, 30, 299.99, 180.00, 8, 'FurnitureCo', 'Warehouse B'),
                ('SKU-004', 'A4 Paper Ream', '500 sheets A4 80gsm', 2, 8, 12.99, 5.50, 50, 'PaperWorld', 'Shelf C1'),
                ('SKU-005', 'USB-C Hub', '7-in-1 USB-C Hub', 1, 65, 79.99, 35.00, 15, 'TechSupplier Inc', 'Shelf A3'),
                ('SKU-006', 'Steel Rod 10mm', 'Mild steel rod 1m length', 3, 200, 8.99, 4.50, 100, 'SteelWorks', 'Warehouse A'),
                ('SKU-007', 'Monitor 27"', '4K IPS Display', 1, 22, 449.99, 310.00, 5, 'DisplayTech', 'Shelf A4'),
                ('SKU-008', 'Cardboard Box L', 'Large shipping box', 5, 7, 2.99, 1.20, 200, 'PackCo', 'Warehouse C'),
                ('SKU-009', 'Keyboard Mechanical', 'RGB Mechanical keyboard', 1, 55, 129.99, 75.00, 10, 'TechSupplier Inc', 'Shelf A2'),
                ('SKU-010', 'Ball Pen Blue 12pk', 'Blue ballpoint pens', 2, 3, 5.99, 2.00, 30, 'StationaryPro', 'Shelf C2'),
            ]
            cur.executemany(
                'INSERT INTO products (sku, name, description, category_id, quantity, unit_price, cost_price, reorder_level, supplier, location) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                products
            )

        mysql.connection.commit()
        cur.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"DB init error: {e}")


# ─── PRODUCTS ──────────────────────────────────────────────────────────────────

@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        cur = mysql.connection.cursor()
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        low_stock = request.args.get('low_stock', '')

        query = '''
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE 1=1
        '''
        params = []

        if search:
            query += ' AND (p.name LIKE %s OR p.sku LIKE %s OR p.supplier LIKE %s)'
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        if category:
            query += ' AND p.category_id = %s'
            params.append(category)
        if low_stock == 'true':
            query += ' AND p.quantity <= p.reorder_level'

        query += ' ORDER BY p.created_at DESC'
        cur.execute(query, params)
        products = cur.fetchall()
        cur.close()
        return jsonify({'success': True, 'data': products})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute('''
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = %s
        ''', (product_id,))
        product = cur.fetchone()
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404

        cur.execute('''
            SELECT t.*, p.name as product_name
            FROM transactions t
            JOIN products p ON t.product_id = p.id
            WHERE t.product_id = %s
            ORDER BY t.created_at DESC LIMIT 20
        ''', (product_id,))
        transactions = cur.fetchall()
        cur.close()
        return jsonify({'success': True, 'data': product, 'transactions': transactions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/products', methods=['POST'])
def create_product():
    try:
        data = request.json
        cur = mysql.connection.cursor()
        cur.execute('''
            INSERT INTO products (sku, name, description, category_id, quantity,
                unit_price, cost_price, reorder_level, supplier, location)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            data['sku'], data['name'], data.get('description', ''),
            data.get('category_id'), data.get('quantity', 0),
            data['unit_price'], data['cost_price'],
            data.get('reorder_level', 10), data.get('supplier', ''), data.get('location', '')
        ))
        product_id = cur.lastrowid

        if data.get('quantity', 0) > 0:
            cur.execute('''
                INSERT INTO transactions (product_id, type, quantity, reference, notes)
                VALUES (%s, 'IN', %s, 'INITIAL', 'Initial stock entry')
            ''', (product_id, data.get('quantity', 0)))

        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True, 'id': product_id}), 201
    except MySQLdb.IntegrityError as e:
        return jsonify({'success': False, 'error': 'SKU already exists'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        data = request.json
        cur = mysql.connection.cursor()
        cur.execute('''
            UPDATE products SET name=%s, description=%s, category_id=%s,
                unit_price=%s, cost_price=%s, reorder_level=%s, supplier=%s, location=%s
            WHERE id=%s
        ''', (
            data['name'], data.get('description', ''), data.get('category_id'),
            data['unit_price'], data['cost_price'],
            data.get('reorder_level', 10), data.get('supplier', ''),
            data.get('location', ''), product_id
        ))
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute('DELETE FROM products WHERE id = %s', (product_id,))
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ─── TRANSACTIONS ──────────────────────────────────────────────────────────────

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    try:
        cur = mysql.connection.cursor()
        limit = request.args.get('limit', 50)
        cur.execute('''
            SELECT t.*, p.name as product_name, p.sku
            FROM transactions t
            JOIN products p ON t.product_id = p.id
            ORDER BY t.created_at DESC
            LIMIT %s
        ''', (limit,))
        transactions = cur.fetchall()
        cur.close()
        return jsonify({'success': True, 'data': transactions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/transactions', methods=['POST'])
def create_transaction():
    try:
        data = request.json
        cur = mysql.connection.cursor()

        cur.execute('SELECT quantity FROM products WHERE id = %s', (data['product_id'],))
        product = cur.fetchone()
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404

        current_qty = product['quantity']
        qty = int(data['quantity'])
        tx_type = data['type']

        if tx_type == 'OUT' and current_qty < qty:
            return jsonify({'success': False, 'error': f'Insufficient stock. Available: {current_qty}'}), 400

        if tx_type == 'IN':
            new_qty = current_qty + qty
        elif tx_type == 'OUT':
            new_qty = current_qty - qty
        else:  # ADJUSTMENT
            new_qty = qty

        cur.execute('UPDATE products SET quantity = %s WHERE id = %s', (new_qty, data['product_id']))
        cur.execute('''
            INSERT INTO transactions (product_id, type, quantity, reference, notes, user)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            data['product_id'], tx_type, qty,
            data.get('reference', ''), data.get('notes', ''),
            data.get('user', 'Admin')
        ))
        mysql.connection.commit()
        cur.close()
        return jsonify({'success': True, 'new_quantity': new_qty}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ─── CATEGORIES ────────────────────────────────────────────────────────────────

@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        cur = mysql.connection.cursor()
        cur.execute('''
            SELECT c.*, COUNT(p.id) as product_count
            FROM categories c
            LEFT JOIN products p ON c.id = p.category_id
            GROUP BY c.id ORDER BY c.name
        ''')
        categories = cur.fetchall()
        cur.close()
        return jsonify({'success': True, 'data': categories})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/categories', methods=['POST'])
def create_category():
    try:
        data = request.json
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO categories (name, description) VALUES (%s, %s)',
                    (data['name'], data.get('description', '')))
        mysql.connection.commit()
        category_id = cur.lastrowid
        cur.close()
        return jsonify({'success': True, 'id': category_id}), 201
    except MySQLdb.IntegrityError:
        return jsonify({'success': False, 'error': 'Category already exists'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ─── DASHBOARD / ANALYTICS ─────────────────────────────────────────────────────

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    try:
        cur = mysql.connection.cursor()

        cur.execute('SELECT COUNT(*) as total FROM products')
        total_products = cur.fetchone()['total']

        cur.execute('SELECT COUNT(*) as low FROM products WHERE quantity <= reorder_level')
        low_stock = cur.fetchone()['low']

        cur.execute('SELECT COUNT(*) as out_of_stock FROM products WHERE quantity = 0')
        out_of_stock = cur.fetchone()['out_of_stock']

        cur.execute('SELECT SUM(quantity * cost_price) as value FROM products')
        inventory_value = cur.fetchone()['value'] or 0

        cur.execute('SELECT SUM(quantity * unit_price) as retail FROM products')
        retail_value = cur.fetchone()['retail'] or 0

        cur.execute('''
            SELECT t.*, p.name as product_name, p.sku
            FROM transactions t JOIN products p ON t.product_id = p.id
            ORDER BY t.created_at DESC LIMIT 10
        ''')
        recent_transactions = cur.fetchall()

        cur.execute('''
            SELECT p.name, p.sku, p.quantity, p.reorder_level,
                   c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.quantity <= p.reorder_level
            ORDER BY p.quantity ASC LIMIT 10
        ''')
        low_stock_products = cur.fetchall()

        cur.execute('''
            SELECT c.name, COUNT(p.id) as count,
                   SUM(p.quantity * p.cost_price) as value
            FROM categories c
            LEFT JOIN products p ON c.id = p.category_id
            GROUP BY c.id, c.name
        ''')
        category_breakdown = cur.fetchall()

        cur.execute('''
            SELECT DATE(created_at) as date,
                   SUM(CASE WHEN type='IN' THEN quantity ELSE 0 END) as stock_in,
                   SUM(CASE WHEN type='OUT' THEN quantity ELSE 0 END) as stock_out
            FROM transactions
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        ''')
        movement_trend = cur.fetchall()

        cur.close()
        return jsonify({
            'success': True,
            'stats': {
                'total_products': total_products,
                'low_stock': low_stock,
                'out_of_stock': out_of_stock,
                'inventory_value': float(inventory_value),
                'retail_value': float(retail_value),
            },
            'recent_transactions': recent_transactions,
            'low_stock_products': low_stock_products,
            'category_breakdown': category_breakdown,
            'movement_trend': movement_trend,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()})


if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
