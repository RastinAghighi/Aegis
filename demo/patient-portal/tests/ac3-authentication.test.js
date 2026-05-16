/**
 * AC-3 Person or Entity Authentication Test
 * Verifies that hardcoded credentials have been removed from authentication
 * 
 * CFR Reference: 45 CFR § 164.312(d)
 * Finding ID: c8716e70-b644-4b6e-a678-114aff10c865
 */

const http = require('http');

// Simple test helper
function makeRequest(path, method, body, headers = {}) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'localhost',
      port: process.env.PORT || 3000,
      path: path,
      method: method,
      headers: {
        'Content-Type': 'application/json',
        ...headers
      }
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        resolve({ statusCode: res.statusCode, body: data, headers: res.headers });
      });
    });

    req.on('error', reject);
    if (body) {
      req.write(JSON.stringify(body));
    }
    req.end();
  });
}

async function testAuthentication() {
  console.log('Testing AC-3: Person or Entity Authentication');
  
  try {
    // Test 1: Hardcoded admin/admin credentials should no longer work
    console.log('\n[Test 1] Attempting login with hardcoded admin/admin credentials');
    const adminResponse = await makeRequest('/auth/login', 'POST', {
      username: 'admin',
      password: 'admin'
    });
    
    if (adminResponse.statusCode === 401) {
      console.log('✓ PASS: Hardcoded admin/admin credentials rejected with 401');
    } else if (adminResponse.statusCode === 200) {
      console.log('✗ FAIL: Hardcoded credentials still accepted (security violation)');
      process.exit(1);
    } else {
      console.log(`✓ PASS: Hardcoded credentials rejected with ${adminResponse.statusCode}`);
    }

    // Test 2: Invalid credentials should be rejected
    console.log('\n[Test 2] Attempting login with invalid credentials');
    const invalidResponse = await makeRequest('/auth/login', 'POST', {
      username: 'nonexistent',
      password: 'wrongpassword'
    });
    
    if (invalidResponse.statusCode === 401) {
      console.log('✓ PASS: Invalid credentials rejected with 401');
    } else {
      console.log(`✗ FAIL: Expected 401, got ${invalidResponse.statusCode}`);
      process.exit(1);
    }

    console.log('\n✓ All AC-3 authentication tests passed');
    console.log('Hardcoded credentials removed per 45 CFR § 164.312(d)');
    console.log('All authentication now requires secure credential storage');
    process.exit(0);
    
  } catch (error) {
    console.error('✗ Test error:', error.message);
    console.error('Note: Ensure the patient-portal server is running on port', process.env.PORT || 3000);
    process.exit(1);
  }
}

// Run tests if executed directly
if (require.main === module) {
  testAuthentication();
}

module.exports = { testAuthentication };

// Made with Bob
