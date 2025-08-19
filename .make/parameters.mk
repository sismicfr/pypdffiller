DOCKER_BUILD_ARGS = --build-arg USER_ID=$(shell id -u) \
					--build-arg GROUP_ID=$(shell id -g)


# Use explicit user id & group along github workflows
ifneq ($(ENV),)
DOCKER_RUN_ARGS = --user "$(shell id -u):$(shell id -g)"
else
DOCKER_RUN_ARGS =
endif
