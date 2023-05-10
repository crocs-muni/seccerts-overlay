# seccerts-overlay

This repository contains metadata binding files used to express N:N relationships between third-party obtained metadata and the certificate they are relevant for.
These metadata are then displayed as part of the [sec-certs](https://seccerts.org/) web.

You can also find header files for some metadata files in this repositories. These header files are referenced in the binding files instead of directly referencing the metadata files.

## JCAlgTestResultsBindings

Bindings in this directory are created by naive matching of security certificates names to jcAlgTest result file names, therefore **they are not meant for production use.**
However, they are still useful as a large bindings dataset for testing purposes.

## Demonstration bindings

Demonstration bindings however are relevant bindings, linking certificates with data actually relevant to the security certification subject.

## Specification

In the specification directory you can find a JSON schemas of the bindings file and headers file formats and a high level diagram of the architecture. 

## Scripts

The scripts folder contains various useful functionality for generating binding files and header files,
verification of jwt tokens, verification of validity of all mandatory fields and automated matching of jcalgtest results to certificates.