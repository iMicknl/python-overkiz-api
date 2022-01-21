# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.209.6/containers/python-3/.devcontainer/base.Dockerfile

# [Choice] Python version (use -bullseye variants on local arm64/Apple Silicon): 3, 3.10, 3.9, 3.8, 3.7, 3.6, 3-bullseye, 3.10-bullseye, 3.9-bullseye, 3.8-bullseye, 3.7-bullseye, 3.6-bullseye, 3-buster, 3.10-buster, 3.9-buster, 3.8-buster, 3.7-buster, 3.6-buster
ARG VARIANT="3.10-bullseye"
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VARIANT}

# [Choice] Node.js version: none, lts/*, 16, 14, 12, 10
ARG NODE_VERSION="none"
RUN if [ "${NODE_VERSION}" != "none" ]; then su vscode -c "umask 0002 && . /usr/local/share/nvm/nvm.sh && nvm install ${NODE_VERSION} 2>&1"; fi

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH "$PATH:/home/vscode/.local/bin"
# RUN poetry config virtualenvs.create false

# RUN poetry completions zsh > ~/.zfunc/_poetry

# /home/vscode/.local/bin

# Install Poetry packages (maybe remove the poetry.lock line if you don't want/have a lock file)
# COPY pyproject.toml ./
# COPY poetry.lock ./
# RUN poetry install --no-interaction

# # Provide a known path for the virtual environment by creating a symlink
# RUN ln -s $(poetry env info --path) /var/my-venv

# # Clean up project files. You can add them with a Docker mount later.
# RUN rm pyproject.toml poetry.lock

# # Hide virtual env prompt
# ENV VIRTUAL_ENV_DISABLE_PROMPT 1

# # Start virtual env when bash starts
# RUN echo 'source /var/my-venv/bin/activate' >> ~/.bashrc

# [Optional] If your pip requirements rarely change, uncomment this section to add them to the image.
# COPY requirements.txt /tmp/pip-tmp/
# RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
#    && rm -rf /tmp/pip-tmp

# [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends <your-package-list-here>

# [Optional] Uncomment this line to install global node packages.
# RUN su vscode -c "source /usr/local/share/nvm/nvm.sh && npm install -g <your-package-here>" 2>&1
