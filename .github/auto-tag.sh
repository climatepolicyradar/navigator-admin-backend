#!/bin/sh

# Argument is going to be the pull request body.
latest_tag=$1
echo "${latest_tag}"

pull_request_body="$2"
echo "${pull_request_body}"

# Check if minor version.
is_minor=false
if [ $(echo "${pull_request_body}" | grep -c "\[x\] Minor version") -gt 0 ]; then
	is_minor=true
fi

# Check if major version.
is_major=false
if [ $(echo "${pull_request_body}" | grep -c "\[x\] Major version") -gt 0 ]; then
	is_major=true
fi

# Check if breaking change.
is_breaking_change=false
if [ $(echo "${pull_request_body}" | grep -c "\[x\] Breaking change") -gt 0 ]; then
	is_breaking_change=true
fi

# If multiple have been checked or none have been checked, don't auto tag.
if { [ "${is_major}" = true ] && [ "${is_minor}" = true ]; } ||
	{ [ "${is_major}" = true ] && [ "${is_breaking_change}" = true ]; } ||
	{ [ "${is_minor}" = true ] && [ "${is_breaking_change}" = true ]; }; then
	echo "Ambiguous tag information. Auto-tagging failed..."
elif { [ "${is_major}" = false ] && [ "${is_minor}" = false ] && [ "${is_breaking_change}" = false ]; }; then
	echo "No tag information found. Auto-tagging failed..."
else
	# Auto-tag based on selected option.
	if [ "${is_minor}" = true ]; then
		echo "Tagging as new minor version..."
	elif [ "${is_major}" = true ]; then
		echo "Tagging as new major version..."
	elif [ "${is_breaking_change}" = true ]; then
		echo "Tagging as new breaking change..."
	fi
fi
