DEV ?= all

.PHONY: doctor deploy build test check clean-meta discovery session-up session-attach session-down

doctor:
	bash harness/doctor.sh $(DEV)

deploy:
	bash harness/deploy.sh $(DEV)

build:
	bash harness/remote-build.sh $(DEV)

test:
	bash harness/remote-test.sh $(DEV)

check:
	bash harness/check.sh $(DEV)

clean-meta:
	bash harness/clean-remote-meta.sh $(DEV)

discovery:
	bash harness/discovery-test.sh

session-up:
	bash harness/session.sh $(DEV) up

session-attach:
	bash harness/session.sh $(DEV) attach

session-down:
	bash harness/session.sh $(DEV) down
