

SRC_MAIN = ./cpm_files/main
SRC_PKG = $(shell find ./cpm_files/*.ZIP -type f)
WORKDIR_BASE := ./tmp
PKG ?= TEST OTHER
ZIPFILES := $(foreach name,$(PKG),$(filter %$(name).ZIP,$(SRC_PKG)))
IMG_DIR = ./img

all: pk_setup pk_unzip disk_8.img pk_clean

disk_8.img: 
	python3 disktool.py -t 8Mb -f -d $(WORKDIR_BASE) -i $(IMG_DIR)/disk_8.img -v

pk_setup:
	@mkdir -p $(IMG_DIR)
	@echo "Preparing tmp directory..."
	@mkdir -p $(WORKDIR_BASE)
	@rm -rf $(WORKDIR_BASE)/*
	@cp -r $(SRC_MAIN)/* $(WORKDIR_BASE)

pk_unzip:
	@$(foreach zipfile,$(ZIPFILES),\
		echo "Unzipping $(zipfile) to $(WORKDIR_BASE)/$(notdir $(basename $(zipfile)))"; \
		mkdir -p $(WORKDIR_BASE)/$(notdir $(basename $(zipfile))); \
		unzip -o $(zipfile) -d $(WORKDIR_BASE); \
	)

pk_clean:
	@echo "Cleaning up tmp directory..."
	@rm -rf $(WORKDIR_BASE)/*
