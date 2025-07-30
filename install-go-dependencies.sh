#!/bin/bash
export GOPATH=$PWD/agrf/gorender/
go install github.com/ahyangyi/gorender/cmd@cdca513
mv gopath/bin/cmd ${GOPATH}/bin/gorender
go install github.com/ahyangyi/cargopositor/cmd@f9051fa
mv gopath/bin/cmd ${GOPATH}/bin/positor
go install github.com/ahyangyi/gandalf/cmd@v1.4.0-ah4
mv gopath/bin/cmd ${GOPATH}/bin/layer-filter
