#!/bin/bash
test_msg="Hello server"
response=$(docker run --rm --network tp0_testing_net alpine sh -c "echo '$test_msg' | nc server 12345")
if [ "$response" = "$test_msg" ]; then
  echo "action: test_echo_server | result: success"
else
  echo "action: test_echo_server | result: fail"
fi
