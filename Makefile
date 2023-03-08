## Spyder Sandbox Makefile (bmake)

ENV_DIR?=	env
ENV_ACTIVATE?=	${ENV_DIR}/bin/activate
ENV_CFG=	${ENV_DIR}/pyvenv.cfg

HOST_PYTHON?=	python3
PROJECT_PY?=	project.py
SETUP_PY?=	setup.py
PIP_REQ?=	requirements.txt
ENV_PROMPT?=	sandbox.spyder

## tool macros
ENV_CMD?=	. ${ENV_ACTIVATE}; ${ENV_DIR}/bin
PROJECT_PYTHON?=	${ENV_CMD}/python3
ENV_PIP?=	${ENV_CMD}/pip

## options for invoking pip
PIP_OPTIONS?=		--no-build-isolation -v --require-virtualenv --disable-pip-version-check
## options for invoking pip-compile [piptools]
PIP_COMPILE_OPTIONS?=	--resolver=backtracking -v --extra dev --pip-args '${PIP_OPTIONS}'
## options for invoking pip-sync [piptools]
PIP_SYNC_OPTIONS?=	-v --ask  --pip-args '${PIP_OPTIONS}'

.PHONY=			all env update sync devinstall

all: env update

env: ${ENV_CFG}

update: ${ENV_CFG} ${PIP_REQ}
	${ENV_PIP} install ${PIP_OPTIONS} --upgrade -r ${PIP_REQ}

sync: update ${ENV_DIR}/bin/pip-compile
	${ENV_CMD}/pip-sync ${PIP_SYNC_OPTIONS}

## pip-sync will uninstall any earlier version after prompt,
## then pip-install will build and install an editable wheel
devinstall: update sync
	${ENV_PIP} install -e .

${ENV_CFG}: ${PROJECT_PY}
	${HOST_PYTHON} ${PROJECT_PY} ensure_env --prompt ${ENV_PROMPT} --envdir ${ENV_DIR}

${ENV_DIR}/bin/pip-compile: ${ENV_CFG}
	${ENV_PIP} install ${PIP_OPTIONS} pip-tools

${ENV_DIR}/bin/doit: ${ENV_CFG}
	${ENV_PIP} install ${PIP_OPTIONS} doit

${PIP_REQ}: ${SETUP_PY} ${ENV_DIR}/bin/pip-compile
	${ENV_CMD}/pip-compile ${PIP_COMPILE_OPTIONS} -o ${PIP_REQ} ${SETUP_PY}


