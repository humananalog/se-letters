const duckdb = require('duckdb');
const path = require('path');

async function testIBcatalogueSchema() {
  const dbPath = path.join(__dirname, 'data', 'IBcatalogue.duckdb');
  const db = new duckdb.Database(dbPath);
  
  console.log('🔍 Testing IBcatalogue database schema...');
  
  try {
    // Test basic connection
    const testResult = await new Promise((resolve, reject) => {
      db.all('SELECT 1 as test', (err, rows) => {
        if (err) reject(err);
        else resolve(rows);
      });
    });
    console.log('✅ Database connection successful:', testResult);
    
    // Check if products table exists
    const tableResult = await new Promise((resolve, reject) => {
      db.all("SELECT name FROM sqlite_master WHERE type='table' AND name='products'", (err, rows) => {
        if (err) reject(err);
        else resolve(rows);
      });
    });
    console.log('📋 Products table check:', tableResult);
    
    // Get schema for products table
    const schemaResult = await new Promise((resolve, reject) => {
      db.all("PRAGMA table_info(products)", (err, rows) => {
        if (err) reject(err);
        else resolve(rows);
      });
    });
    console.log('📊 Products table schema:');
    schemaResult.forEach(col => {
      console.log(`  - ${col.name} (${col.type})`);
    });
    
    // Test a sample query
    const sampleResult = await new Promise((resolve, reject) => {
      db.all("SELECT PRODUCT_IDENTIFIER, RANGE_LABEL, SERVICE_BUSINESS_VALUE FROM products LIMIT 3", (err, rows) => {
        if (err) reject(err);
        else resolve(rows);
      });
    });
    console.log('🔍 Sample query result:', sampleResult);
    
  } catch (error) {
    console.error('❌ Error:', error);
  } finally {
    db.close();
  }
}

testIBcatalogueSchema(); 