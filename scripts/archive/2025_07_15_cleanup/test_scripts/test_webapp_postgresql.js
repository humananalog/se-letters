#!/usr/bin/env node
/**
 * Test Webapp PostgreSQL Connection
 */

const { Pool } = require('pg');

async function testWebappDatabase() {
  console.log('🔍 Testing webapp PostgreSQL connection...');
  
  const pool = new Pool({
    connectionString: 'postgresql://alexandre@localhost:5432/se_letters_dev',
    max: 20,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000,
  });

  try {
    // Test basic connectivity
    const result = await pool.query('SELECT COUNT(*) as count FROM letters');
    console.log(`✅ Database connection successful - ${result.rows[0].count} letters found`);
    
    // Test letter statistics
    const stats = await pool.query(`
      SELECT 
        COUNT(*) as total_letters,
        COUNT(CASE WHEN status = 'processed' THEN 1 END) as processed_count,
        AVG(extraction_confidence) as avg_confidence
      FROM letters
    `);
    
    console.log('📊 Letter statistics:');
    console.log(`  Total letters: ${stats.rows[0].total_letters}`);
    console.log(`  Processed: ${stats.rows[0].processed_count}`);
    console.log(`  Avg confidence: ${stats.rows[0].avg_confidence || 0}`);
    
    // Test search functionality
    const searchResult = await pool.query(`
      SELECT id, document_name, created_at 
      FROM letters 
      ORDER BY created_at DESC 
      LIMIT 5
    `);
    
    console.log('📝 Recent letters:');
    searchResult.rows.forEach(letter => {
      console.log(`  - ${letter.document_name} (ID: ${letter.id})`);
    });
    
    console.log('✅ All webapp database tests passed!');
    
  } catch (error) {
    console.error('❌ Webapp database test failed:', error);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

testWebappDatabase(); 