<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/class.exception.php -->
# PHP: Exception

(PHP 5, PHP 7, PHP 8)

## Introduction

**Exception** is the base class for
exceptions that can be handled during normal operation.

## Class synopsis

class ****Exception****
implements
Throwable {

/\* Properties \*/

protected
string
$message = "";

private
string
$string = "";

protected
int
$code;

protected
string
$file = "";

protected
int
$line;

private
array
$trace = [];

private
?Throwable
$previous = null;

/\* Methods \*/

public function \_\_construct(string `$message` = "", int `$code` = 0, ?Throwable `$previous` = **`null`**)

final public function getMessage(): string

final public function getPrevious(): ?Throwable

final public function getCode(): int

final public function getFile(): string

final public function getLine(): int

final public function getTrace(): array

final public function getTraceAsString(): string

public function \_\_toString(): string

private function \_\_clone(): void

}

## Properties

message
:   The exception message

code
:   The exception code

file
:   The filename where the exception was created

line
:   The line where the exception was created

previous
:   The previously thrown exception

string
:   The string representation of the stack trace

trace
:   The stack trace as an array

## Table of Contents

* Exception::\_\_construct — Construct the exception
* Exception::getMessage — Gets the Exception message
* Exception::getPrevious — Returns previous Throwable
* Exception::getCode — Gets the Exception code
* Exception::getFile — Gets the file in which the exception was created
* Exception::getLine — Gets the line in which the exception was created
* Exception::getTrace — Gets the stack trace
* Exception::getTraceAsString — Gets the stack trace as a string
* Exception::\_\_toString — String representation of the exception
* Exception::\_\_clone — Clone the exception

### Found A Problem?
