/**
 * AC-1 Access Control Test
 * Verifies that GET /patients/:id requires authentication
 * 
 * CFR Reference: 45 CFR § 164.312(a)(1)
 * Finding ID: de6e15cf-6bc2-4700-aa6d-67c3091c05b0
 */

const http = require('http');

// Simple test helper
function makeRequest(path, headers = {}) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'localhost',
      port: process.env.PORT || 3000,
      path: path,
      method: 'GET',
      headers: headers
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        resolve({ statusCode: res.statusCode, body: data, headers: res.headers });
      });
    });

    req.on('error', reject);
    req.end();
  });
}

async function testAccessControl() {
  console.log('Testing AC-1: Access Control on GET /patients/:id');
  
  try {
    // Test 1: Unauthenticated request should be rejected
    console.log('\n[Test 1] Unauthenticated request to GET /patients/1');
    const unauthResponse = await makeRequest('/patients/1');
    
    if (unauthResponse.statusCode === 401) {
      console.log('✓ PASS: Unauthenticated request rejected with 401');
    } else {
      console.log(`✗ FAIL: Expected 401, got ${unauthResponse.statusCode}`);
      process.exit(1);
    }

    // Test 2: Request with invalid token should be rejected
    console.log('\n[Test 2] Request with invalid token to GET /patients/1');
    const invalidTokenResponse = await makeRequest('/patients/1', {
      'Authorization': 'Bearer invalid-token-12345'
    });
    
    if (invalidTokenResponse.statusCode === 401) {
      console.log('✓ PASS: Invalid token rejected with 401');
    } else {
      console.log(`✗ FAIL: Expected 401, got ${invalidTokenResponse.statusCode}`);
      process.exit(1);
    }

    console.log('\n✓ All AC-1 access control tests passed');
    console.log('The GET /patients/:id endpoint now requires authentication per 45 CFR § 164.312(a)(1)');
    process.exit(0);
    
  } catch (error) {
    console.error('✗ Test error:', error.message);
    console.error('Note: Ensure the patient-portal server is running on port', process.env.PORT || 3000);
    process.exit(1);
  }
}

// Run tests if executed directly
if (require.main === module) {
  testAccessControl();
}

module.exports = { testAccessControl };

// Made with Bob
