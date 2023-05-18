coverage run --source OleBackend,utils,user,task,picbed,review,video,advertise -m pytest --junit-xml=xunit-reports/xunit-result.xml
ret=$?
coverage xml -o coverage-reports/coverage.xml
coverage report
exit $ret