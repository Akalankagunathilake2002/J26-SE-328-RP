<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: PHP -->
<!-- source: PHP Manual (PHP Documentation Group) -->
<!-- license: CC BY 3.0 -->
<!-- url: https://www.php.net/manual/en/faq.passwords.php -->
# PHP: Password Hashing

This section explains the reasons behind using hashing functions
to secure passwords, as well as how to do so effectively.

1. Why should passwords supplied by users be hashed?
2. Why are common hashing functions such as md5 and
   sha1 unsuitable for passwords?
3. How should passwords be hashed, if the common hash functions are
   not suitable?
4. What is a salt?
5. How are salts stored?

**Why should passwords supplied by users be hashed?**
:   Password hashing is one of the most basic security considerations that
    must be made when designing any application or service that accepts passwords
    from users. Without hashing, any passwords that are stored
    can be stolen if the data store is compromised, and
    then immediately used to compromise not only the application or service, but also
    the accounts of users on other services, if they do not use
    unique passwords.

    By applying a hashing algorithm to the user's passwords before storing
    them, it becomes implausible for any attacker to
    determine the original password, while still being able to compare
    the resulting hash to the original password in the future.

    It is important to note, however, that hashing passwords only protects
    them from being compromised in the data store, but does not necessarily
    protect them from being intercepted by malicious code injected into the
    application or service itself.

**Why are common hashing functions such as md5() and sha1() unsuitable for passwords?**
:   Hashing algorithms such as MD5, SHA1 and SHA256 are designed to be
    very fast and efficient. With modern techniques and computer equipment,
    it has become trivial to "brute force" the output of these algorithms,
    in order to determine the original input.

    Because of how quickly a modern computer can "reverse" these hashing
    algorithms, many security professionals strongly suggest against
    their use for password hashing.

**How should passwords be hashed, if the common hash functions are not suitable?**
:   When hashing passwords, the two most important considerations are the
    computational expense and the salt. The more computationally expensive
    the hashing algorithm, the longer it will take to brute force its
    output.

    PHP provides
    a native password hashing API that
    safely handles both hashing
    and verifying passwords
    in a secure manner.

    The suggested algorithm to use when hashing passwords is Blowfish, which
    is also the default used by the password hashing API, as it is
    significantly more computationally expensive than MD5 or SHA1, while
    still being scalable.

    The crypt() function is also available for password
    hashing, but it is only recommended for interoperability with other
    systems.
    Instead, it is strongly encouraged to use the
    native password hashing API
    whenever possible.

**What is a salt?**
:   A cryptographic salt is data which is applied during the hashing process
    in order to eliminate the possibility of the output being looked up
    in a list of pre-calculated pairs of hashes and their input, known as
    a rainbow table.

    In simpler terms, a salt is a bit of additional data which makes
    hashes significantly more difficult to crack. There are a number of
    services online which provide extensive lists of pre-computed hashes, as
    well as the original input for those hashes. The use of a salt makes it
    implausible or impossible to find the resulting hash in one of these
    lists.

    password\_hash() will create a random salt if one
    isn't provided, and this is generally the easiest and most secure
    approach.

**How are salts stored?**
:   When using password\_hash() or
    crypt(), the return value includes the salt as part
    of the generated hash. This value should be stored verbatim in the
    database, as it includes information about the hash function that was
    used and can then be given directly to
    password\_verify() when verifying passwords.

    **Warning**

    password\_verify() should always be used instead
    of re-hashing and comparing the result to a stored hash in order
    to avoid timing attacks.

    The following diagram shows the format of a return value from
    crypt() or password\_hash(). As can
    be seen, they are self-contained, with all the information on the
    algorithm and salt required for future password verification.

### Found A Problem?
